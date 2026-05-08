## 📸 效果演示

![demo](demo.gif)


# 📡 PaperPilot

> 基于多智能体（Multi-Agent）的 AI 学术论文调研助手
> 输入研究方向，自动完成论文搜索、下载、阅读、分析与中英双语调研报告生成。

支持人工确认、历史记录、多阶段工作流与实时流式输出。

---

# ✨ 功能特性

## 🔍 智能论文搜索

* 自然语言输入研究方向
* 大模型自动提取英文关键词
* 自动过滤歧义词与低相关结果
* 基于 OpenAlex 检索高质量论文

## 👨‍💻 人工交互确认

* 搜索完成后展示候选论文列表
* 用户可勾选需要深入分析的论文
* 避免无关论文进入后续流程

## 📄 PDF 全文解析

* 自动下载论文 PDF
* 使用 GROBID 提取结构化章节：

  * Abstract
  * Discussion
  * Conclusion

## 🧠 结构化论文分析

自动提取：

* 核心研究问题
* 方法原理
* 关键实验结果
* 作者提出的局限性
* 潜在改进方向

## 🌏 中英双语报告生成

* 自动生成中文调研报告
* 使用 Ollama 本地模型翻译英文版
* 支持逐字流式输出（SSE）

## 📚 引用与历史记录

* 自动生成脚注引用 `[1][2][3]`
* 左侧论文列表与引用编号对应
* SQLite 持久化保存历史调研
* 支持浮窗查看历史报告，不中断当前任务

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

| 模块     | 技术方案                                |
| ------ | ----------------------------------- |
| 后端框架   | Python + FastAPI                    |
| 工作流编排  | LangGraph                           |
| 大模型分析  | OpenAI API / DeepSeek               |
| 本地翻译模型 | Ollama + qwen2.5:7b                 |
| 论文搜索   | OpenAlex API                        |
| PDF 解析 | GROBID                              |
| 实时通信   | SSE（sse-starlette）                  |
| 前端     | Vue 3 + Vite + Pinia + Tailwind CSS |
| 数据存储   | SQLite                              |
| 依赖管理   | Poetry                              |
| 容器化    | Docker                              |

---

# 🚀 快速开始

## 运行环境

请确保本机已安装：

* Python 3.12+
* Poetry
* Docker
* Ollama

---

## 1️⃣ 克隆项目

```bash
git clone https://github.com/cquestcLsq/paper-agent.git

cd paper-agent
```

---

## 2️⃣ 配置环境变量

复制配置模板：

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
├── main.py                 # FastAPI 入口 + SSE 接口 + 确认接口
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
│       ├── views/Home.vue  # 首页（三栏布局）
│       ├── stores/research.js # Pinia 状态管理 + SSE 解析
│       └── components/     # 搜索栏、状态栏、论文卡片、报告视图
├── output/                 # 每次调研自动存档
└── history.db              # SQLite 历史记录数据库
```

---

# 💡 使用说明

## 1. 输入研究方向

例如：

```text
帮我调研近3年关于大语言模型 Agent 的 5 篇论文
```

---

## 2. 确认候选论文

系统搜索完成后：

* 中间栏展示论文列表
* 用户勾选需要分析的论文
* 点击「确认选择」

---

## 3. 自动分析与生成报告

系统将自动完成：

* PDF 下载
* 章节解析
* 结构化分析
* 调研报告生成

---

## 4. 实时查看结果

右侧报告区域支持：

* 逐字流式输出
* 中英文切换
* 一键复制 Markdown

---

## 5. 查看历史记录

点击右上角「历史记录」即可：

* 查看历史调研
* 恢复之前的报告
* 不影响当前任务

---

# 📝 输出结果示例

每次调研会自动生成独立目录：

```text
output/20260507_153000_xxxx/
├── original_sections/
│   ├── 01_xxx.txt
│   └── 02_xxx.txt
│
├── search_results.json
├── extracted_data.json
└── final_report.md
```

---

# 🌟 项目亮点

* 多智能体协同工作流
* 支持 Human-in-the-Loop
* 本地 + 云端混合推理
* 面向真实科研调研场景
* 全流程自动化论文分析
* 可扩展 Agent 架构

---

# 🙏 致谢

* OpenAlex —— 开放学术论文索引平台
* GROBID —— PDF 结构化解析工具
* LangGraph —— 多智能体工作流框架
* Ollama —— 本地大模型运行平台
* Tailwind CSS —— 实用优先 CSS 框架

---

