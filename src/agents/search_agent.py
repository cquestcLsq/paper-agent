"""
Search Agent - 使用 OpenAlex API 搜索论文
大模型负责理解用户意图、提取关键词，代码负责拼检索式、调 API
"""
import os
import re
import json
from datetime import datetime
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from dotenv import load_dotenv
import ollama
from src.core.state_models import State, ExecutionState, BackToFrontData
from src.agents.openalex_search import search_openalex
from src.core.prompts import SEARCH_KEYWORDS_SYSTEM, TRANSLATE_SUMMARIES_USER
load_dotenv()


# ==========================================
# 1. Pydantic 模型：大模型只提取关键词
# ==========================================
class SearchKeywords(BaseModel):
    core_keywords: list[str] = Field(description="核心搜索关键词（英文），2-4个")
    exclude_keywords: list[str] = Field(default_factory=list, description="排除词")
    max_results: int = Field(default=5, description="搜索篇数")
    year_start: int = Field(default=2000, description="最早年份，如 2000")
    explanation: str = Field(description="检索策略说明（中文）")


# ==========================================
# 2. 规范化论文字段
# ==========================================
def _normalize_paper(p: dict) -> dict:
    """确保所有字段都有安全默认值，避免 None 值传播"""
    return {
        "title": p.get("title") or "",
        "year": p.get("year") or "",
        "citation_count": p.get("citation_count") or 0,
        "authors": p.get("authors") or [],
        "url": p.get("url") or "",
        "pdf_url": p.get("pdf_url") or "",
        "summary": p.get("summary") or "",
        "summary_cn": p.get("summary_cn") or "",
        "published": p.get("published") or "",
    }


# ==========================================
# 3. 翻译摘要
# ==========================================
def _translate_summaries(papers: list) -> list:
    """逐篇翻译摘要，加超时保护"""
    for p in papers:
        summary = p.get("summary", "")
        if not summary:
            p["summary_cn"] = ""
            continue
        try:
            response = ollama.chat(
                model=os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"),
                messages=[{
                    "role": "user",
                    "content": TRANSLATE_SUMMARIES_USER.format(summary=summary)
                }],
                options={"timeout": 30}
            )
            raw = response.get("message", {}).get("content")
            p["summary_cn"] = raw.strip() if raw else summary
        except Exception:
            p["summary_cn"] = summary
    return papers


# ==========================================
# 4. 搜索节点主逻辑
# ==========================================
async def search_node(state: State, queue) -> State:
    """搜索智能体节点：理解意图 → 提取关键词 → OpenAlex 搜索 → 翻译摘要 → 推送"""

    current_state = state["value"]
    current_state.current_step = ExecutionState.SEARCHING

    user_intent = current_state.user_query or "RAG retrieval augmented generation"

    # ===== 创建任务目录 =====
    task_dir = f"output/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_intent[:10].replace(' ', '_')}"
    os.makedirs(task_dir, exist_ok=True)
    current_state.task_dir = task_dir

    # 推送：开始分析
    await queue.put(BackToFrontData(
        step=ExecutionState.SEARCHING,
        state="initializing",
        data="[Search Agent] 正在分析用户意图，提取搜索关键词..."
    ))

    # 初始化大模型客户端
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL")
    )
    model_name = os.environ.get("MODEL_NAME", "deepseek-ai/DeepSeek-V3")

    try:
        # ===== 第1步：大模型提取关键词 =====
        completion = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SEARCH_KEYWORDS_SYSTEM},
                {"role": "user", "content": f"用户输入：{user_intent}"}
            ],
            max_tokens=300,
            temperature=0.1,
        )

        content = completion.choices[0].message.content
        if not content:
            raise ValueError("大模型返回为空")
        content = content.strip()

        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

        try:
            data = json.loads(content)
            keywords = SearchKeywords(
                core_keywords=data.get("core_keywords", [user_intent]),
                exclude_keywords=data.get("exclude_keywords", []),
                max_results=int(data.get("max_results", 5)),
                year_start=int(data.get("year_start", 2000)),
                explanation=data.get("explanation", "根据用户意图提取关键词"),
            )
        except Exception:
            await queue.put(BackToFrontData(
                step=ExecutionState.SEARCHING,
                state="error",
                data="[Search Agent] 关键词提取失败，无法继续搜索。"
            ))
            return {"value": current_state}

        await queue.put(BackToFrontData(
            step=ExecutionState.SEARCHING,
            state="processing",
            data=f"[Search Agent] 搜索策略：{keywords.explanation}\n关键词: {keywords.core_keywords}\n排除: {keywords.exclude_keywords}\n正在搜索 OpenAlex..."
        ))

        # ===== 第2步：OpenAlex 搜索 =====
        papers = await search_openalex(
            keywords=keywords.core_keywords,
            max_results=keywords.max_results,
            require_pdf=True,
            year_start=keywords.year_start
        )

        # 规范化所有字段
        papers = [_normalize_paper(p) for p in papers]

        # 排除干扰词
        if keywords.exclude_keywords and papers:
            papers = [
                p for p in papers
                if not any(
                    exclude.lower() in p["title"].lower()
                    or exclude.lower() in p["summary"].lower()
                    for exclude in keywords.exclude_keywords
                )
            ]

        # 过滤：保留有摘要的，或者有可下载 PDF 的
        def _has_downloadable_pdf(pdf_url: str) -> bool:
            if not pdf_url:
                return False
            return (
                pdf_url.startswith("https://arxiv.org/")
                or pdf_url.startswith("https://content.openalex.org/")
            )

        papers = [p for p in papers if p["summary"] or _has_downloadable_pdf(p["pdf_url"])]

        # 如果不够，放宽条件补搜
        if len(papers) < keywords.max_results:
            extra = await search_openalex(
                keywords=keywords.core_keywords,
                max_results=keywords.max_results * 2,
                require_pdf=False
            )
            extra = [_normalize_paper(p) for p in extra]
            existing_titles = {p["title"] for p in papers}
            extra = [p for p in extra if p["summary"] and p["title"] not in existing_titles]
            papers.extend(extra[:keywords.max_results - len(papers)])

        current_state.search_results = papers

        # ===== 第3步：翻译摘要 =====
        await queue.put(BackToFrontData(
            step=ExecutionState.SEARCHING,
            state="processing",
            data="[Search Agent] 正在翻译论文摘要为中文..."
        ))
        papers = _translate_summaries(papers)
        current_state.search_results = papers

        # ===== 存档 =====
        search_file = os.path.join(task_dir, "search_results.json")
        with open(search_file, "w", encoding="utf-8") as f:
            json.dump([
                {
                    "title": p["title"],
                    "year": p["year"],
                    "citation_count": p["citation_count"],
                    "authors": p["authors"],
                    "url": p["url"],
                    "pdf_url": p["pdf_url"],
                    "published": p["published"],
                }
                for p in papers
            ], f, ensure_ascii=False, indent=2, default=str)

        # ===== 第4步：一次性推送 =====
        if papers:
            paper_items = [
                {
                    "title": p["title"],
                    "year": p["year"],
                    "citations": p["citation_count"],
                    "url": p["url"],
                    "abstract": p["summary_cn"],
                }
                for p in papers
            ]

            await queue.put(BackToFrontData(
                step=ExecutionState.SEARCHING,
                state="result",
                data=json.dumps({"type": "papers", "papers": paper_items}, ensure_ascii=False)
            ))

            await queue.put(BackToFrontData(
                step=ExecutionState.SEARCHING,
                state="completed",
                data=f"[Search Agent] 成功获取 {len(papers)} 篇论文！\n📁 已保存到: {search_file}"
            ))
        else:
            await queue.put(BackToFrontData(
                step=ExecutionState.SEARCHING,
                state="completed",
                data="[Search Agent] 未找到相关论文，请尝试调整搜索关键词。"
            ))

    except Exception as e:
        await queue.put(BackToFrontData(
            step=ExecutionState.SEARCHING,
            state="error",
            data=f"[Search Agent] 搜索失败: {str(e)}"
        ))

    return {"value": current_state}