"""
Read Agent - 下载 PDF、提取原文章节（摘要 + 结论）
使用 GROBID 进行章节解析，不调大模型，纯工程操作
"""
import os
import re
import asyncio
import httpx
from dotenv import load_dotenv
import xml.etree.ElementTree as ET_GROBID
from src.core.state_models import State, ExecutionState, BackToFrontData

load_dotenv()


# ==========================================
# 主节点
# ==========================================
async def read_node(state: State, queue) -> State:
    """读取节点：下载 PDF + 提取摘要和结论 + 存档"""
    current_state = state["value"]
    current_state.current_step = ExecutionState.READING
    
    papers = current_state.search_results
    if not papers:
        await queue.put(BackToFrontData(
            step=ExecutionState.READING, state="error", data="未找到待阅读论文"
        ))
        return {"value": current_state}
    
    await queue.put(BackToFrontData(
        step=ExecutionState.READING,
        state="processing",
        data=f"[Read Agent] 开始下载 {len(papers)} 篇论文的 PDF 并提取章节..."
    ))
    
    # ===== 并发下载 + 提取 =====
    tasks = [_download_and_extract(p) for p in papers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 整理结果
    read_results = []
    original_sections = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"[WARN] 第 {i+1} 篇 PDF 提取失败: {r}")
            read_results.append({
                "title": papers[i].get("title", "未知"),
                "authors": papers[i].get("authors", []),
                "summary": papers[i].get("summary", ""),
                "original_sections": "",
            })
            original_sections.append({
                "title": papers[i].get("title", "未知"),
                "summary": papers[i].get("summary", ""),
                "original_sections": "PDF 提取失败",
            })
        else:
            read_results.append(r)
            original_sections.append(r)
    
    # 存入 state（给 analyze_node 用）
    current_state.read_results = read_results
    
    # ===== 存档 original_sections/ =====
    task_dir = current_state.task_dir
    if task_dir:
        sections_dir = os.path.join(task_dir, "original_sections")
        os.makedirs(sections_dir, exist_ok=True)
        for i, sec in enumerate(original_sections, 1):
            safe_title = sec["title"][:30]\
            .replace("/", "_")\
            .replace("\\", "_")\
            .replace(":", "_")\
            .replace("*", "")\
            .replace("?", "")\
            .replace("\"", "")\
            .replace("<", "")\
            .replace(">", "")\
            .replace("|", "_")
            sections_file = os.path.join(sections_dir, f"{i:02d}_{safe_title}.txt")
            
            content = f"标题：{sec['title']}\n\n"
            content += f"作者：{sec.get('authors', '')}\n\n"
            content += f"摘要：\n{_wrap_text(sec.get('summary', ''))}\n\n"
            content += f"结论章节原文：\n{_wrap_text(sec.get('original_sections', ''))}"
            
            with open(sections_file, "w", encoding="utf-8") as f:
                f.write(content)
        
        print(f"📁 原始章节已保存到: {sections_dir}")
    
    success_count = sum(1 for r in read_results if r.get("original_sections"))
    msg = f"[Read Agent] PDF 下载完成！成功提取 {success_count} 篇原文。"
    await queue.put(BackToFrontData(step=ExecutionState.READING, state="completed", data=msg))
    
    return {"value": current_state}


# ==========================================
# 下载 + 提取单篇
# ==========================================
async def _download_and_extract(paper: dict) -> dict:
    """下载单篇 PDF 并通过 GROBID 提取摘要 + 结论"""
    title = paper.get("title", "")
    summary = paper.get("summary", "")
    pdf_url = paper.get("pdf_url", "")
    authors = paper.get("authors", [])
    
    extracted_summary = ""
    key_sections = ""
    
    if pdf_url:
        # 1. 下载 PDF
        pdf_bytes = await _download_pdf(pdf_url)
        if pdf_bytes:
            # 2. 调用 GROBID 解析
            grobid_result = await _parse_with_grobid(pdf_bytes)
            extracted_summary = grobid_result.get("abstract", "")
            # 合并 conclusion + discussion
            conclusion = grobid_result.get("conclusion", "")
            discussion = grobid_result.get("discussion", "")
            key_sections = f"{discussion}\n\n{conclusion}".strip()
    
    return {
        "title": title,
        "summary": extracted_summary if extracted_summary else summary,
        "authors": authors,
        "original_sections": key_sections,
    }


# ==========================================
# PDF 下载
# ==========================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def _download_pdf(pdf_url: str) -> bytes | None:
    try:
        url = pdf_url
        
        # content.openalex.org 需要 API Key
        if "content.openalex.org" in url:
            api_key = os.environ.get("OPENALEX_API_KEY", "")
            if api_key:
                url += f"?api_key={api_key}"
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.content
    except Exception:
        pass
    return None

# ==========================================
# GROBID 解析
# ==========================================
async def _parse_with_grobid(pdf_bytes: bytes) -> dict:
    """调用 GROBID API 解析 PDF，返回各章节字典"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8070/api/processFulltextDocument",
                files={"input": ("paper.pdf", pdf_bytes, "application/pdf")},
                data={
                    "consolidateHeader": "1",
                    "segmentSentences": "0",
                }
            )

        if response.status_code != 200:
            return {}
        
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        root = ET_GROBID.fromstring(response.text)
        
        sections = {}
        
        # ===== 1. 提取摘要（大小写不敏感）=====
        abstract_elem = None
        for child in root.iter():
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag.lower() == 'abstract':
                abstract_elem = child
                break
        
        if abstract_elem is not None:
            abstract_parts = []
            for p in abstract_elem.findall(".//tei:p", ns):
                if p.text:
                    abstract_parts.append(p.text.strip())
            if abstract_parts:
                sections["abstract"] = "\n\n".join(abstract_parts)
        
        # ===== 2. 遍历所有带 <head> 的子 div，用标题作为章节名 =====
        for div in root.findall(".//tei:div[tei:head]", ns):
            head = div.find("tei:head", ns)
            if head is None or not head.text:
                continue
            
            # 去掉编号 "1.", "2.1.", "6." 等，保留纯文本标题
            section_name = re.sub(r'^\s*[\d\.]+\s*', '', head.text.strip())
            if not section_name:
                continue
            
            # 提取该章节的所有文字
            text_parts = []
            for p in div.findall(".//tei:p", ns):
                if p.text:
                    text_parts.append(p.text.strip())
            
            if text_parts:
                key = section_name.lower()
                # 模糊匹配：包含 conclusion → 统一归为 conclusion
                if 'conclusion' in key:
                    key = 'conclusion'
                elif 'discussion' in key:
                    key = 'discussion'
                sections[key] = "\n\n".join(text_parts)
        
        # ===== 3. 也提取有 type 属性的 div（funding, references 等）=====
        for div in root.findall(".//tei:div[@type]", ns):
            div_type = div.get("type", "").lower()
            if div_type in sections:
                continue
            text_parts = []
            for p in div.findall(".//tei:p", ns):
                if p.text:
                    text_parts.append(p.text.strip())
            if text_parts:
                sections[div_type] = "\n\n".join(text_parts)
        
        # ===== 4. 合并 Discussion 的子章节 =====
        discussion_start = None
        all_divs = root.findall(f".//{{{ns['tei']}}}div[{{{ns['tei']}}}head]")
        
        for i, div in enumerate(all_divs):
            head = div.find(f"{{{ns['tei']}}}head")
            if head is None or not head.text:
                continue

            name = re.sub(r'^\s*[\d\.]+\s*', '', head.text.strip()).lower()
            
            if 'discussion' in name and 'conclusion' not in name:
                discussion_start = i
                break
        
        if discussion_start is not None:
            discussion_texts = []
            
            for div in all_divs[discussion_start:]:
                head = div.find(f"{{{ns['tei']}}}head")
                if head is None or not head.text:
                    continue
                
                name = re.sub(r'^\s*[\d\.]+\s*', '', head.text.strip()).lower()
                
                stop_keywords = {"conclusion", "conclusions", "references", "acknowledgment", "appendix", "funding"}
                if name in stop_keywords or 'conclusion' in name:
                    break
                
                for p in div.findall(f".//{{{ns['tei']}}}p"):
                    if p.text:
                        discussion_texts.append(p.text.strip())
            
            if discussion_texts:
                sections["discussion"] = "\n\n".join(discussion_texts)
        
        return sections
    
    except Exception as e:
        print(f"[WARN] GROBID 解析失败: {e}")
        return {}


# ==========================================
# 文字格式化
# ==========================================
def _wrap_text(text: str, width: int = 80) -> str:
    """每 width 个字符换行，不截断单词"""
    if not text:
        return ""
    
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return '\n'.join(lines)