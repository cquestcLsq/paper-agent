"""
FastAPI 与 SSE 实时推送接口
"""
import os
import asyncio
import traceback
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from src.agents.orchestrator import PaperAgentOrchestrator
from src.core.state_models import StateValue, BackToFrontData

app = FastAPI(title="论文调研助手")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 多用户支持：按 session_id 存储状态
app.state.sessions = {}


def _get_session(session_id: str) -> dict:
    """获取或创建 session"""
    if session_id not in app.state.sessions:
        app.state.sessions[session_id] = {
            "queue": None,
            "orchestrator": None,
        }
    return app.state.sessions[session_id]


async def safe_run_graph(coro, queue):
    try:
        await coro
    except Exception as e:
        print(f"\n❌ [后台任务致命错误] 执行失败: {e}")
        traceback.print_exc()
        try:
            await queue.put(BackToFrontData(
                step="error",
                state="error",
                data=f"后台执行发生异常: {str(e)}"
            ))
        except:
            pass


@app.post('/api/confirm_papers')
async def confirm_papers(request: dict):
    titles = request.get("titles", [])
    session_id = request.get("session_id", "default")
    session = _get_session(session_id)
    orchestrator = session.get("orchestrator")

    if not orchestrator or not titles:
        return {"status": "error", "message": "没有可确认的论文"}

    current = orchestrator.app.get_state(orchestrator.config).values
    all_papers = current["value"].search_results

    titles_lower = [t.strip().lower() for t in titles]
    filtered = [p for p in all_papers if p["title"].strip().lower() in titles_lower]

    new_value = current["value"].model_copy(
        update={"search_results": filtered, "confirmed": True}
    )
    orchestrator.app.update_state(orchestrator.config, {"value": new_value})

    return {"status": "ok", "count": len(filtered)}


@app.get('/api/research/continue')
async def research_continue(request: Request, session_id: str = "default"):
    session = _get_session(session_id)
    state_queue = session.get("queue")
    orchestrator = session.get("orchestrator")

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    print("⚠️ [SSE] 前端 /continue 连接已断开！")
                    break
                try:
                    state_data = await asyncio.wait_for(state_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                yield {"data": state_data.model_dump_json()}
                step_val = state_data.step.value if hasattr(state_data.step, "value") else state_data.step
                if step_val == "writing" and state_data.state in ["completed", "error"]:
                    print("✅ [SSE] 最终报告生成完毕，关闭 /continue 通道。")
                    break
        except Exception as e:
            print(f"❌ [SSE] continue 发生异常: {e}")

    event_source = EventSourceResponse(event_generator(), media_type="text/event-stream")
    asyncio.create_task(safe_run_graph(orchestrator.continue_from_read(), state_queue))
    return event_source


@app.get('/api/research')
async def research_stream(request: Request, query: str, max_results: int = 5, session_id: str = "default"):
    state_queue = asyncio.Queue()

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    print("⚠️ [SSE] 前端 /research 主连接已断开！")
                    break
                try:
                    state_data = await asyncio.wait_for(state_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                yield {"data": state_data.model_dump_json()}
                step_val = state_data.step.value if hasattr(state_data.step, "value") else state_data.step
                if step_val == "searching" and state_data.state == "completed":
                    print("⏸️ [SSE] 搜索完成，挂起等待用户确认论文...")
                    break
        except Exception as e:
            print(f"❌ [SSE] research 发生异常: {e}")

    event_source = EventSourceResponse(event_generator(), media_type="text/event-stream")

    orchestrator = PaperAgentOrchestrator(state_queue=state_queue)

    # 存储到当前 session
    session = _get_session(session_id)
    session["queue"] = state_queue
    session["orchestrator"] = orchestrator

    asyncio.create_task(safe_run_graph(orchestrator.run(user_request=query, max_results=max_results), state_queue))
    return event_source


@app.get('/api/health')
async def health():
    return {"status": "ok"}


frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)