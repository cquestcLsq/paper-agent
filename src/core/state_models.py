from typing import TypedDict, Optional, List, Dict, Any  # 导入需要的工具：TypedDict给字典做类型提示，Optional/List/Dict是Python类型注解
from enum import Enum  # Enum：枚举，用来定义固定的状态（比如空闲、搜索中、完成）
from pydantic import BaseModel, Field  # BaseModel, Field：Pydantic数据验证，保证数据格式正确

'''
定义核心状态模型:
这是系统的灵魂。多智能体协同不是靠互相调用函数，而是共同维护和修改一个全局的 State 字典。

简单理解：
所有智能体（搜索、阅读、分析、写作）都不直接通信，
它们只修改这个共享的 State，
然后通过 state_queue 把结果实时推送给前端。
'''

# ====================== 1. 系统运行阶段枚举 ======================
# 作用：定义整个智能体工作流有哪些步骤，固定值，防止写错
class ExecutionState(str, Enum):
    IDLE = "idle"  # 空闲状态，还没开始任务
    SEARCHING = "searching"  # 正在搜索文献
    READING = "reading"  # 正在阅读文献
    ANALYSING = "analysing"  # 正在分析内容
    WRITING = "writing"  # 正在写报告
    COMPLETED = "completed"  # 任务全部完成

# ====================== 2. 推送给前端的数据模型 ======================
# 作用：定义【后端 → 前端】实时推送的数据格式（SSE 流式输出）
class BackToFrontData(BaseModel):
    step: ExecutionState  # 当前走到哪个阶段（searching / reading 等）
    state: str = Field(description="当前状态描述，如 'initializing', 'processing', 'completed'")  # 当前状态描述：初始化中 / 处理中 / 已完成
    data: Optional[Any] = None  # 要传给前端的数据（可以是文献、结果、进度等）

# ====================== 3. 智能体共享的全局状态 ======================
# 作用：所有智能体都读写这个对象，这是整个系统的“共享大脑”
class StateValue(BaseModel):
    current_step: ExecutionState = ExecutionState.IDLE  # 当前系统正在执行哪个步骤（默认空闲）
    user_query: str = ""               # 用户输入的搜索关键词
    task_dir: str = ""                 # 任务目录
    max_results: int = 5               # 最大搜索结果数
    confirmed: bool = False            # 用户是否已确认论文选择
    search_results: List[Dict] = Field(default_factory=list)  # 文献搜索结果（列表，里面存多篇文献的字典）
    read_results: List[Dict] = Field(default_factory=list)    # 文献阅读结果
    extracted_data: Optional[Dict] = None  # 从文献里提取的关键信息（知识点、方法、结论等）
    report_content: str = ""  # 最终生成的报告内容

# ====================== 4. LangGraph 工作流使用的总状态 ======================
# 作用：LangGraph 框架要求的状态格式，
class State(TypedDict):
    value: StateValue  # 共享状态：所有智能体读写的数据都在这里