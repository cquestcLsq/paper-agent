# 📡 PaperPilot

> 基于多智能体（Multi-Agent）的 AI 学术论文调研助手  
> 输入研究方向，自动完成论文搜索、下载、阅读、分析与中英双语调研报告生成。

支持：

- Human-in-the-Loop 人工确认
- 多阶段 Agent 工作流
- SSE 实时流式输出
- 历史记录持久化
- 多用户并行调研

---

# 📸 效果演示

![demo](example.gif)

---

# ✨ 功能特性

## 🔍 智能论文搜索

- 自然语言输入研究方向
- 大模型自动提取英文关键词
- 自动过滤歧义词与低相关结果
- 基于 OpenAlex 检索高质量论文
- 优先返回近几年研究成果

---

## 👨‍💻 Human-in-the-Loop 人工确认

搜索完成后：

- 展示候选论文列表（标题可点击跳转原论文）
- 用户勾选需要深入分析的论文
- 避免无关论文进入后续流程
- 减少 Token 与 PDF 下载开销

---

## 📄 PDF 全文解析

系统自动：

- 下载论文 PDF
- 调用 GROBID 解析章节结构
- 提取：
  - Abstract
  - Discussion
  - Conclusion

并保留原始章节文本。

---

## 🧠 结构化分析

自动提取：

- 核心研究问题
- 方法原理
- 关键实验结果
- 作者提出的局限性
- 潜在改进方向

---

## 🌏 中英双语报告生成

自动生成：

- 中文调研报告
- 英文翻译版本

支持：

- SSE 逐字流式输出
- Markdown 一键复制
- 自动脚注引用 `[1][2][3]`

---

## 📚 历史记录与多用户

支持：

- SQLite 持久化保存历史调研
- 浮窗查看历史报告
- 不中断当前任务
- 多标签页并行调研
- 多用户会话隔离

---

# 🧩 工作流程

```text
用户输入研究方向
        ↓
LLM 提取关键词
        ↓
OpenAlex 搜索论文
        ↓
Ollama 翻译摘要
        ↓
用户确认论文
        ↓
下载 PDF + GROBID 解析
        ↓
LLM 结构化分析
        ↓
生成中文调研报告
        ↓
Ollama 翻译英文
        ↓
SSE 流式推送
        ↓
Vue 3 实时渲染
```

---

# 🛠 技术栈

| 模块 | 技术方案 |
|---|---|
| 后端框架 | Python + FastAPI |
| 工作流编排 | LangGraph |
| 大模型分析 | OpenAI API / DeepSeek |
| 本地翻译模型 | Ollama + qwen2.5:7b |
| 论文搜索 | OpenAlex API |
| PDF 解析 | GROBID |
| 实时通信 | SSE（sse-starlette） |
| 前端 | Vue 3 + Vite + Pinia + Tailwind CSS |
| 数据存储 | SQLite |
| 依赖管理 | Poetry |
| 容器化 | Docker |

---

# 🚀 快速开始

## 运行环境

请确保本机已安装：

- Python 3.12+
- Poetry
- Docker
- Ollama

---

## 1️⃣ 克隆项目

```bash
git clone https://github.com/cquestcLsq/paper-agent.git

cd paperpilot
```

---

## 2️⃣ 配置环境变量

复制配置模板：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
OPENAI_API_KEY=sk-xxx

OPENAI_BASE_URL=https://api.deepseek.com/v1

MODEL_NAME=deepseek-ai/DeepSeek-V3

OPENALEX_API_KEY=your_openalex_api_key

REGISTERED_EMAIL=your_email@example.com

OLLAMA_MODEL=qwen2.5:7b
```

---

## 3️⃣ 安装依赖

```bash
poetry install
```

---

## 4️⃣ 启动 GROBID

```bash
docker run -d \
  -p 8070:8070 \
  --name grobid \
  lfoppiano/grobid:0.8.0
```

---

## 5️⃣ 拉取本地翻译模型

```bash
ollama pull qwen2.5:7b
```

---

## 6️⃣ 启动后端服务

```bash
poetry run python main.py
```

---

## 7️⃣ 启动前端

```bash
cd frontend

npm install

npm run dev
```

浏览器访问：

```text
http://localhost:3000
```

---

# 📂 项目结构

```text
.
├── main.py                         # FastAPI 入口 + SSE 接口 + 用户确认接口
│
├── src/
│
│   ├── core/                      # 核心配置与状态定义
│   │   ├── state_models.py        # LangGraph State 数据结构
│   │   └── prompts.py             # 所有 Prompt 集中管理
│   │
│   ├── agents/                    # 多智能体实现
│   │   ├── orchestrator.py        # LangGraph 工作流编排入口
│   │   │
│   │   ├── search_agent.py        # 关键词提取 + OpenAlex 搜索 + 摘要翻译
│   │   │
│   │   ├── read_agent.py          # PDF 下载 + GROBID 章节解析
│   │   │
│   │   ├── analyze_agent.py       # 提取研究问题/方法/结果/局限性
│   │   │
│   │   ├── write_agent.py         # 调研报告生成 + 英文翻译
│   │   │
│   │   └── openalex_search.py     # OpenAlex API 封装
│   │
│   └── services/
│       └── db.py                  # SQLite 历史记录服务
│
├── frontend/                      # Vue3 前端
│   └── src/
│       │
│       ├── views/
│       │   └── Home.vue           # 三栏主界面
│       │
│       ├── stores/
│       │   └── research.js        # Pinia 状态管理 + SSE 数据流处理
│       │
│       └── components/            # 前端组件
│           ├── SearchBar.vue      # 搜索输入框
│           ├── PaperCard.vue      # 论文卡片
│           ├── ReportView.vue     # 调研报告视图
│           └── HistoryModal.vue   # 历史记录弹窗
│
├── output/                        # 每次调研自动生成的输出目录
│
└── history.db                     # SQLite 历史数据库
```

---

# 💡 使用说明

## 1️⃣ 输入研究方向

例如：

```text
帮我搜索5篇近几年关于RAG技术的论文
```

---

## 2️⃣ 确认候选论文

系统搜索完成后：

- 中间栏展示候选论文
- 用户勾选需要分析的论文
- 点击「确认选择」

---

## 3️⃣ 自动分析与生成报告

系统将自动完成：

- PDF 下载
- GROBID 章节解析
- 结构化内容分析
- 中英双语报告生成

---

## 4️⃣ 实时查看结果

右侧报告区域支持：

- 逐字流式输出
- 中英文切换
- Markdown 一键复制

---

## 5️⃣ 查看历史记录

点击右上角「历史记录」即可：

- 查看历史调研结果
- 恢复之前的报告
- 不影响当前任务

---

# 📝 输出结果示例

每次调研会自动生成独立目录：

```text
output/20260507_153000_ISAR/
├── original_sections/             # 提取的原始章节文本
│   ├── 01_xxx.txt
│   └── 02_xxx.txt
│
├── search_results.json            # 搜索得到的论文元数据
│
├── extracted_data.json            # 大模型结构化提取结果
│
└── final_report.md                # 最终中英双语调研报告
```

---

# 🌟 项目亮点

- 多智能体协同工作流
- Human-in-the-Loop 交互式调研
- 本地 + 云端混合推理
- 面向真实科研调研场景
- 全流程自动化论文分析
- 可扩展 Agent 架构
- 支持流式实时生成

---

# 🙏 致谢

- OpenAlex —— 开放学术论文索引平台
- GROBID —— PDF 结构化解析工具
- LangGraph —— 多智能体工作流框架
- Ollama —— 本地大模型运行平台
- Tailwind CSS —— 实用优先 CSS 框架

---
