"""
Analyze Agent - 将论文信息发给大模型，提取结构化信息
"""
import os
import re
import json
import asyncio
import httpx
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from dotenv import load_dotenv

from src.core.state_models import State, ExecutionState, BackToFrontData
from src.core.prompts import ANALYZE_PAPER_SYSTEM
load_dotenv()


# ==========================================
# 数据模型
# ==========================================
class KeyMethodology(BaseModel):
    name: str = Field(description="方法名称")
    principle: str = Field(description="核心原理")


class ExtractedPaperData(BaseModel):
    title: str = Field(description="论文标题")
    authors: str = Field(default="", description="论文作者")
    core_problem: str = Field(description="核心痛点")
    key_methodology: KeyMethodology = Field(description="关键方法")
    main_results: str = Field(description="主要结果")
    stated_limitations: str = Field(description="原文明确提到的局限性（如果没有则填'未提及'）")
    potential_limitations: str = Field(description="基于方法论的潜在局限性")


# ==========================================
# 主节点
# ==========================================
async def analyze_node(state: State, queue) -> State:
    """分析节点：并发调大模型提取结构化信息"""
    
    current_state = state["value"]
    current_state.current_step = ExecutionState.ANALYSING
    
    read_results = current_state.read_results
    if not read_results:
        await queue.put(BackToFrontData(
            step=ExecutionState.ANALYSING, state="error", data="没有可分析的论文"
        ))
        return {"value": current_state}
    
    await queue.put(BackToFrontData(
        step=ExecutionState.ANALYSING,
        state="processing",
        data=f"[Analyze Agent] 并发分析 {len(read_results)} 篇论文..."
    ))
    
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        timeout=httpx.Timeout(60.0, connect=10.0)
    )
    model_name = os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-V3")
    
    tasks = [_analyze_single_paper(client, model_name, r) for r in read_results]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"[WARN] 第 {i+1} 篇分析失败: {r}")
        elif "error" not in r:
            successful.append(r)
    
    current_state.extracted_data = {"papers": successful}
    
    # ===== 存档 =====
    task_dir = current_state.task_dir
    if task_dir:
        extracted_file = os.path.join(task_dir, "extracted_data.json")
        with open(extracted_file, "w", encoding="utf-8") as f:
            json.dump(current_state.extracted_data, f, ensure_ascii=False, indent=2, default=str)
        
        await queue.put(BackToFrontData(
            step=ExecutionState.ANALYSING,
            state="completed",
            data=f"成功提取 {len(successful)} 篇论文信息\n📁 已保存到: {extracted_file}"
        ))
    
    return {"value": current_state}


# ==========================================
# 单篇分析
# ==========================================
async def _analyze_single_paper(client, model_name, paper_data):
    """分析单篇论文"""
    system_prompt = ANALYZE_PAPER_SYSTEM
    
    user_content = f"【标题】: {paper_data.get('title', '')}"

    authors = paper_data.get("authors", [])
    if authors:
        user_content += f"\n【作者】: {', '.join(authors[0])}"

    user_content += f"\n【摘要】: {paper_data.get('summary', '')}"

    if paper_data.get("original_sections"):
        user_content += f"\n【正文关键章节】:\n{paper_data['original_sections']}"
    
    for attempt in range(3):
        try:
            completion = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1200
            )
            raw = completion.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = re.sub(r'^```(?:json)?\s*', '', raw)
                raw = re.sub(r'\s*```$', '', raw)

            result = ExtractedPaperData.model_validate_json(raw).model_dump()
            result["authors"] = ", ".join(paper_data.get("authors", [])[0]) 
            return result
        except Exception as e:
            if attempt == 2:
                return {
                    "title": paper_data.get("title", "未知"),
                    "authors": ", ".join(paper_data.get("authors", [])[0]), 
                    "error": str(e)
                }