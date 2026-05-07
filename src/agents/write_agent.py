"""
Writing Agent - 根据提取结果生成中文调研报告，Ollama 本地翻译英文
"""
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from src.core.state_models import State, ExecutionState, BackToFrontData
from src.core.prompts import WRITE_REPORT_SYSTEM, TRANSLATE_REPORT_USER
from ollama import AsyncClient
from src.services.db import save_research
load_dotenv()


def build_user_content(user_query: str, papers_data: list[dict], search_map: dict) -> str:
    """把提取结果拼成大模型的输入"""
    content = f"用户查询：{user_query}\n\n"
    content += f"以下是从 {len(papers_data)} 篇论文中提取的结构化信息：\n\n"
    
    for i, paper in enumerate(papers_data, 1):
        title = paper.get("title", "")
        km = paper.get("key_methodology", {})

        original_authors = search_map.get(title, {}).get("authors", [])
        first_author = original_authors[0] if original_authors else "未知"
        
        content += f"""### [{i}] {title}

        - **作者**：{first_author}
        - **核心问题**：{paper.get('core_problem', '未知')}
        - **方法**：{km.get('name', '未知')}
        - **原理**：{km.get('principle', '未知')}
        - **主要结果**：{paper.get('main_results', '未知')}
        - **原文局限性**：{paper.get('stated_limitations', '未提及')}
        - **潜在局限性**：{paper.get('potential_limitations', '未提及')}

        """
    
    return content


async def write_node(state: State, queue) -> State:
    """调研报告写作节点：中文生成 + Ollama 本地翻译"""

    current_state = state["value"]
    current_state.current_step = ExecutionState.WRITING

    search_results = current_state.search_results
    extracted_data = current_state.extracted_data

    search_map = {p["title"]: p for p in search_results}
    
    if not extracted_data or not extracted_data.get("papers"):
        await queue.put(BackToFrontData(
            step=ExecutionState.WRITING,
            state="error",
            data="[Writing Agent] 没有可用的提取结果。"
        ))
        return {"value": current_state}
    
    papers_data = extracted_data["papers"]
    user_query = current_state.user_query
    
    await queue.put(BackToFrontData(
        step=ExecutionState.WRITING,
        state="processing",
        data=f"[Writing Agent] 正在基于 {len(papers_data)} 篇论文撰写调研报告..."
    ))
    
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL")
    )
    model_name = os.environ.get("MODEL_NAME", "deepseek-ai/DeepSeek-V3")
    
    system_prompt = WRITE_REPORT_SYSTEM

    user_content = build_user_content(user_query, papers_data, search_map)
    
    try:
        # ===== Step 1: 生成中文报告 =====
        stream = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3,
            max_tokens=3000,
            stream=True
        )
        
        full_report = ""
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_report += delta
                await queue.put(BackToFrontData(
                    step=ExecutionState.WRITING,
                    state="streaming",
                    data=delta
                ))
        
        current_state.report_content = full_report
        
        # ===== Step 2: 通知前端中文生成完毕 =====
        await queue.put(BackToFrontData(
            step=ExecutionState.WRITING,
            state="separator",
            data="---"
        ))
        
        # ===== Step 3: Ollama 流式翻译 + 逐字推送 =====
        await queue.put(BackToFrontData(
            step=ExecutionState.WRITING,
            state="processing",
            data="[Writing Agent] 正在本地翻译英文版本..."
        ))

        ollama_client = AsyncClient()
        stream = await ollama_client.chat(
            model=os.environ.get("OLLAMA_MODEL", "qwen2.5:7b"),
            messages=[{
                "role": "user",
                    "content": TRANSLATE_REPORT_USER.format(full_report=full_report)
            }],
            stream=True
        )

        report_en = ""
        async for chunk in stream:
            delta = chunk["message"]["content"]
            report_en += delta
            await queue.put(BackToFrontData(
                step=ExecutionState.WRITING,
                state="streaming",
                data=delta
            ))
        task_dir = current_state.task_dir
        if task_dir:
            report_file = os.path.join(task_dir, "final_report.md")
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(full_report + "\n\n---\n\n" + report_en)
        
        await queue.put(BackToFrontData(
            step=ExecutionState.WRITING,
            state="completed",
            data=f"\n\n📁 报告已保存到: {report_file}" if task_dir else "\n\n✅ 报告生成完成！"
        ))
        # 保存历史记录

        try:
            save_research(
                query=current_state.user_query,
                papers=current_state.search_results,
                report_zh=full_report,
                report_en=report_en
            )
        except Exception:
            pass  # 保存失败不影响主流程
    
    except Exception as e:
        await queue.put(BackToFrontData(
            step=ExecutionState.WRITING,
            state="error",
            data=f"[Writing Agent] 报告生成失败: {str(e)}"
        ))
    
    return {"value": current_state}