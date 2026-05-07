"""
OpenAlex 论文搜索模块
API 文档：https://docs.openalex.org/
注册邮箱后可享 100 RPS（请求参数加 mailto=你的邮箱）
"""
import httpx
from typing import List, Optional

import os
from dotenv import load_dotenv
load_dotenv()

# 注册邮箱（提升频率限制到 100 RPS）
REGISTERED_EMAIL = os.environ.get("REGISTERED_EMAIL", "")


async def search_openalex(
    keywords: List[str],
    max_results: int = 5,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    require_pdf: bool = True
) -> List[dict]:
    """
    搜索 OpenAlex

    参数:
        keywords: 关键词列表，如 ['ISAR', 'clutter suppression']
        max_results: 最大返回数量
        year_start: 最早年份
        year_end: 最晚年份
        require_pdf: 是否只返回有公开 PDF 的论文（默认 True）

    返回:
        论文列表
    """
    # ===== 拼接搜索语句 =====
    search_query = " ".join(keywords)

    # ===== 构建过滤条件 =====
    filters = []
    if require_pdf:
        filters.append("is_oa:true")
    if year_start:
        filters.append(f"publication_year:>{year_start - 1}")
    if year_end:
        filters.append(f"publication_year:<{year_end + 1}")

    filter_str = ",".join(filters) if filters else None

    # ===== 构建请求 =====
    url = "https://api.openalex.org/works"
    params = {
        "search": search_query,
        "per_page": max_results,
        "mailto": REGISTERED_EMAIL,
    }
    if filter_str:
        params["filter"] = filter_str

    # ===== 发送请求 =====
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise Exception(f"OpenAlex API 请求失败，状态码: {response.status_code}")

    data = response.json()
    papers = []

    # ===== 解析结果 =====
    for work in data.get("results", []):
        # 提取基本信息
        title = work.get("title", "")
        abstract = ""
        if work.get("abstract_inverted_index"):
            abstract = _decode_inverted_index(work["abstract_inverted_index"])

        # 发表年份
        year = work.get("publication_year", "")

        # 引用数
        citation_count = work.get("cited_by_count", 0)

        # 作者
        authors = []
        for authorship in work.get("authorships", []):
            author = authorship.get("author", {})
            if author.get("display_name"):
                authors.append(author["display_name"])

        # PDF 链接：优先用 OpenAlex 托管版，其次用期刊原版
        pdf_url = None
        content_urls = work.get("content_urls")
        primary_location = work.get("primary_location", {})
        if content_urls and content_urls.get("pdf"):
            pdf_url = content_urls["pdf"]
        elif primary_location and primary_location.get("pdf_url"):
            pdf_url = primary_location["pdf_url"]
        elif work.get("open_access", {}).get("oa_url"):
            pdf_url = work["open_access"]["oa_url"]

        # arXiv ID
        arxiv_id = None
        if primary_location:
            source = primary_location.get("source", {})
            if source and source.get("display_name") == "arXiv":
                landing_url = primary_location.get("landing_page_url", "")
                if "arxiv.org/abs/" in landing_url:
                    arxiv_id = landing_url.split("arxiv.org/abs/")[-1].split("?")[0]

        # 论文链接
        url_link = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else work.get("doi", "")

        # 领域
        fields_of_study = []
        for concept in work.get("concepts", []):
            if concept.get("display_name"):
                fields_of_study.append(concept["display_name"])

        papers.append({
            "title": title,
            "summary": abstract,
            "year": year,
            "citation_count": citation_count,
            "authors": authors,
            "fields_of_study": fields_of_study,
            "is_open_access": work.get("open_access", {}).get("is_oa", False),
            "arxiv_id": arxiv_id,
            "url": url_link,
            "pdf_url": pdf_url,
            "published": str(year) if year else "",
        })

    return papers


def _decode_inverted_index(inverted_index: dict) -> str:
    """
    将 OpenAlex 的倒排索引摘要还原为正常文本
    
    OpenAlex 摘要格式: {"word1": [0, 5], "word2": [1, 6], ...}
    其中数字代表该词在摘要中的位置
    """
    if not inverted_index:
        return ""

    position_to_word = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            position_to_word[pos] = word

    sorted_positions = sorted(position_to_word.keys())
    words = [position_to_word[pos] for pos in sorted_positions]

    return " ".join(words)