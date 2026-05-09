## README.md

```markdown
# 📡 PaperPilot —— 基于多智能体的学术论文调研助手

输入研究方向，AI 自动搜索、下载、阅读、分析论文，生成中英双语调研报告。支持人工交互确认、历史记录、多用户并行。

## 📸 效果演示

![demo](example.gif)

## ✨ 核心功能

- **智能搜索**：自然语言输入，大模型自动提取英文关键词，排除歧义词，优先返回近几年文献
- **人工确认**：搜索后展示论文列表，用户勾选确认后继续分析
- **摘要翻译**：Ollama 本地翻译英文摘要为中文
- **PDF 全文提取**：GROBID 自动识别章节结构，提取摘要、讨论、结论
- **结构化分析**：提取核心问题、方法原理、主要结果、原文局限性、潜在局限性
- **双语报告**：中文报告 + Ollama 本地翻译英文，逐字流式推送
- **脚注引用**：[1][2] 自动对应左侧论文列表
- **历史记录**：SQLite 持久化，浮窗查看历史报告（不中断当前调研）
- **多用户支持**：不同标签页/浏览器同时调研，互不干扰

## 🧩 工作流程

```
用户输入 → 大模型提取关键词 → OpenAlex 搜索 → Ollama 翻译摘要
    ↓ 人工确认论文
GROBID 解析 PDF 章节 → 大模型结构化提取 → 中文报告生成 → Ollama 本地翻译英文
    ↓ SSE 逐字推送
Vue 3 前端实时渲染
```

## 🛠 技术栈

| 层级 | 技术 |
|:--|:--|
| 后端框架 | Python / FastAPI |
| 工作流编排 | LangGraph（条件边 + 条件入口点 + MemorySaver Checkpointer） |
| 大模型 | OpenAI API（云端分析）+ Ollama / qwen2.5:7b（本地翻译） |
| 论文搜索 | OpenAlex API |
| PDF 解析 | GROBID（Docker 部署） |
| 实时推送 | SSE（sse-starlette） |
| 前端 | Vue 3 + Vite + Pinia + Tailwind CSS |
| 历史记录 | SQLite |
| 多用户 | session_id + app.state.sessions |
| 依赖管理 | Poetry |
| 容器化 | Docker（GROBID） |

## 🚀 快速开始

### 前提

- Python 3.12+
- Poetry
- Docker（用于 GROBID）
- Ollama（用于本地翻译）

### 1. 克隆项目

```bash
git clone https://github.com/cquestcLsq/paper-agent.git
cd paper-agent
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# 大模型配置（示例为 DeepSeek，也可换成 OpenAI 官方或其他兼容接口）
OPENAI_API_KEY=sk-你的密钥
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-ai/DeepSeek-V3

# OpenAlex 配置（用于下载 PDF）
OPENALEX_API_KEY=你的OpenAlex_API_Key

# 注册邮箱（提升搜索频率限制）
REGISTERED_EMAIL=你的邮箱@example.com

# Ollama 本地翻译模型
OLLAMA_MODEL=qwen2.5:7b
```

### 3. 安装依赖

```bash
poetry install
```

### 4. 启动 GROBID

```bash
docker run -d -p 8070:8070 --name grobid lfoppiano/grobid:0.8.0
```

### 5. 拉取 Ollama 翻译模型

```bash
ollama pull qwen2.5:7b
```

### 6. 启动后端

```bash
poetry run python main.py
```

### 7. 启动前端

```bash
cd frontend
npm install
npx vite
```

浏览器打开 `http://localhost:3000`。

## 💡 使用说明

1. 在搜索框输入研究方向，如"帮我搜索5篇近几年关于RAG技术的论文"
2. 等待搜索完成，论文列表展示在中间栏
3. 勾选要分析的论文，点"确认选择"
4. 系统自动下载 PDF、提取章节、分析、撰写报告
5. 报告逐字流式输出在右侧，支持中英文切换和复制
6. 点击右上角"历史记录"可查看之前的调研结果

## 📂 项目结构

```
.
├── main.py                 # FastAPI 入口 + SSE 接口 + 确认接口 + 历史接口
├── src/
│   ├── core/
│   │   ├── state_models.py # LangGraph State 定义 + 数据模型
│   │   └── prompts.py      # 所有提示词集中管理
│   ├── agents/
│   │   ├── orchestrator.py # LangGraph 工作流编排
│   │   ├── search_agent.py # 搜索节点：关键词提取 + 摘要翻译
│   │   ├── read_agent.py   # PDF 下载 + GROBID 章节提取
│   │   ├── analyze_agent.py# 结构化提取
│   │   ├── write_agent.py  # 报告生成 + Ollama 翻译
│   │   └── openalex_search.py # OpenAlex API 封装
│   └── services/
│       └── db.py           # SQLite 历史记录服务
├── frontend/               # Vue 3 前端
│   └── src/
│       ├── views/Home.vue  # 首页（三栏布局 + 历史记录浮窗）
│       ├── stores/research.js # Pinia 状态管理 + SSE 解析 + 多用户支持
│       └── components/     # 搜索栏、状态栏、论文卡片、报告视图
├── output/                 # 每次调研自动存档
└── history.db              # SQLite 历史记录数据库
```

## 📝 每次调研输出

```
output/20260509_124034_帮我搜索3篇近几年关/
├── original_sections/      # 提取的 PDF 原文
│   ├── 01_xxx.txt
│   └── 02_xxx.txt
├── search_results.json     # 搜索到的论文元数据
├── extracted_data.json     # 大模型结构化提取结果
└── final_report.md         # 最终调研报告（中英双语）
```

## 🙏 致谢

- [OpenAlex](https://openalex.org/) — 免费开放的学术论文索引
- [GROBID](https://grobid.readthedocs.io/) — 机器学习驱动的 PDF 解析
- [LangGraph](https://langchain-ai.github.io/langgraph/) — 多智能体工作流框架
- [Ollama](https://ollama.com/) — 本地大模型部署
- [Tailwind CSS](https://tailwindcss.com/) — 实用优先的 CSS 框架
```
