"""
使用 LangGraph 编排工作流
支持人工确认条件边 + 条件入口点 + Checkpointer
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.core.state_models import State, StateValue, ExecutionState
from src.agents.search_agent import search_node
from src.agents.read_agent import read_node
from src.agents.analyze_agent import analyze_node
from src.agents.write_agent import write_node
import asyncio

def should_continue(state: State) -> str:
    if state["value"].confirmed:
        return "read_node"
    return END


def where_to_start(state: State) -> str:
    if state["value"].confirmed:
        return "read_node"
    return "search_node"


class PaperAgentOrchestrator:
    def __init__(self, state_queue: asyncio.Queue):
        self.state_queue = state_queue
        self.checkpointer = MemorySaver()
        self.workflow = StateGraph(State)
        self._build_graph()

    def _build_graph(self):
        # 把 queue 通过闭包传给节点
        queue = self.state_queue
        
        async def search_node_with_queue(state: State) -> State:
            return await search_node(state, queue)
        
        async def read_node_with_queue(state: State) -> State:
            return await read_node(state, queue)
        
        async def analyze_node_with_queue(state: State) -> State:
            return await analyze_node(state, queue)
        
        async def write_node_with_queue(state: State) -> State:
            return await write_node(state, queue)

        self.workflow.add_node("search_node", search_node_with_queue)
        self.workflow.add_node("read_node", read_node_with_queue)
        self.workflow.add_node("analyze_node", analyze_node_with_queue)
        self.workflow.add_node("write_node", write_node_with_queue)

        self.workflow.set_conditional_entry_point(
            where_to_start,
            {"search_node": "search_node", "read_node": "read_node"}
        )
        
        self.workflow.add_conditional_edges(
            "search_node",
            should_continue,
            {"read_node": "read_node", END: END}
        )
        
        self.workflow.add_edge("read_node", "analyze_node")
        self.workflow.add_edge("analyze_node", "write_node")
        self.workflow.add_edge("write_node", END)

        self.app = self.workflow.compile(checkpointer=self.checkpointer)

    @property
    def config(self):
        return {"configurable": {"thread_id": "research-1"}}

    async def run(self, user_request: str, max_results: int = 5):
        initial_state = {
            "value": StateValue(user_query=user_request, max_results=max_results)
        }
        async for output in self.app.astream(initial_state, self.config):
            pass

    async def continue_from_read(self):
        async for output in self.app.astream(None, self.config):
            pass

    def update_search_results(self, filtered_papers: list):
        current = self.app.get_state(self.config).values
        new_state = {
            "value": current["value"].model_copy(
                update={"search_results": filtered_papers, "confirmed": True}
            )
        }
        self.app.update_state(self.config, new_state)