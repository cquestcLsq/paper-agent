# 📡 PaperPilot

> 基于多智能体（Multi-Agent）的学术论文调研助手  
> 输入研究方向，AI 自动完成论文搜索、阅读、分析与中英双语综述生成。

<p align="center">

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Vue](https://img.shields.io/badge/Vue3-42b883)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange)
![License](https://img.shields.io/badge/License-MIT-red)

</p>

---

## ✨ 项目特性

### 🔍 智能论文检索

- 自然语言输入研究方向
- 自动提取英文关键词
- OpenAlex 多条件搜索
- 自动过滤歧义词
- 优先返回近年高相关论文
- 支持人工勾选确认待分析论文

### 📖 自动论文阅读

- 自动下载论文 PDF
- GROBID 提取结构化章节
- 自动识别摘要、方法、实验、结论
- 摘要自动翻译为中文
- 保留原始章节文本

### 🧠 多智能体分析

自动提取：

- 核心研究问题
- 方法原理
- 关键实验结果
- 作者提出的局限性
- 潜在问题与改进方向

支持：

- 多 Agent 协同工作
- LangGraph 工作流调度
- 条件边 + Checkpoint 恢复

### 📝 双语报告生成

- 自动生成中文调研报告
- Ollama 本地翻译英文版
- SSE 逐字流式输出
- 自动脚注引用 `[1][2]`
- 支持一键复制

### 🗂 系统能力

- SQLite 历史记录持久化
- 多用户并行会话
- 调研结果自动归档
- Vue3 三栏实时界面
- 不同浏览器/标签页互不干扰

---

## 📸 效果演示

![demo](example.gif)

---

# 💡 为什么选择 PaperPilot

相比传统 AI 对话工具，PaperPilot 不只是“回答问题”，而是真正完成完整的论文调研流程：

✅ 自动搜索并筛选论文  
✅ 自动下载与解析 PDF  
✅ 多论文交叉分析  
✅ 结构化提取核心内容  
✅ 自动生成中英双语综述  
✅ 本地模型翻译，降低 API 成本  
✅ 支持历史记录与结果归档  

适用于：

- 🎓 研究生文献调研
- 🤖 AI 论文速读
- 🧪 企业技术预研
- 📈 技术趋势分析
- 📚 技术博客素材整理

---

# 🧩 工作流程

```text
用户输入研究方向
        ↓
大模型提取关键词
        ↓
OpenAlex 搜索论文
        ↓
用户勾选确认论文
        ↓
下载 PDF + GROBID 解析章节
        ↓
多 Agent 结构化分析
        ↓
生成中文调研报告
        ↓
Ollama 本地翻译英文
        ↓
SSE 实时流式输出
```

---

# ⚙️ 技术栈

| 模块 | 技术 |
|---|---|
| 后端框架 | FastAPI + Python |
| 工作流编排 | LangGraph |
| 大模型 | OpenAI API / DeepSeek |
| 本地模型 | Ollama（qwen2.5:7b） |
| 论文搜索 | OpenAlex |
| PDF 解析 | GROBID |
| 前端 | Vue3 + Pinia + Tailwind CSS |
| 实时推送 | SSE |
| 数据库 | SQLite |
| 依赖管理 | Poetry |

---

# 🚀 快速开始

## 1. 克隆项目

```bash
git clone https://github.com/cquestcLsq/paper-agent.git
cd paper-agent
```

---

## 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# 大模型配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-ai/DeepSeek-V3

# OpenAlex
OPENALEX_API_KEY=your_openalex_key
REGISTERED_EMAIL=your_email@example.com

# Ollama
OLLAMA_MODEL=qwen2.5:7b
```

---

## 3. 安装依赖

```bash
poetry install
```

---

## 4. 启动 GROBID

```bash
docker run -d -p 8070:8070 \
  --name grobid \
  lfoppiano/grobid:0.8.0
```

---

## 5. 拉取 Ollama 模型

```bash
ollama pull qwen2.5:7b
```

---

## 6. 启动后端

```bash
poetry run python main.py
```

---

## 7. 启动前端

```bash
cd frontend

npm install
npx vite
```

浏览器打开：

```text
http://localhost:3000
```

---

# 💡 使用说明

1. 输入研究方向

例如：

```text
帮我调研近几年关于 RAG 的关键论文
```

2. 系统自动搜索论文

3. 勾选需要分析的论文

4. 自动下载 PDF 并解析章节

5. 多智能体协同生成调研报告

6. 实时查看中英双语输出

7. 在历史记录中查看过去调研结果

---

# 📂 项目结构

```text
.
├── main.py
├── src/
│   ├── core/
│   │   ├── state_models.py
│   │   └── prompts.py
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── search_agent.py
│   │   ├── read_agent.py
│   │   ├── analyze_agent.py
│   │   ├── write_agent.py
│   │   └── openalex_search.py
│   └── services/
│       └── db.py
├── frontend/
├── output/
└── history.db
```

---

# 📄 调研输出示例

```text
output/
└── 20260509_xxx/
    ├── original_sections/
    ├── search_results.json
    ├── extracted_data.json
    └── final_report.md
```

每次调研会自动保存：

- 原始论文章节
- 搜索结果元数据
- 结构化提取结果
- 最终中英双语报告

---


# 🙏 致谢

- [OpenAlex](https://openalex.org/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [GROBID](https://grobid.readthedocs.io/)
- [Ollama](https://ollama.com/)
- [Tailwind CSS](https://tailwindcss.com/)

---
