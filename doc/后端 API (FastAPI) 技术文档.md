后端 API (FastAPI) 技术文档 (V5.0)
本文档描述了如何使用 FastAPI 构建一个 API 服务器，该服务器作为 wg.py 脚本的“API 包装器”，为 Web 前端提供服务。

FastAPI 后端 (wg-server) 技术文档
1. 🎯 核心目标
解耦： 将 wg.py 的核心业务逻辑（引擎）与 UI（前端）分离。

API 驱动： 提供一组 RESTful API 端点 (Endpoints)，让任何 HTTP 客户端（如 Vue 应用）都能操作 wg 的功能。

异步处理： 确保 pandoc 或 git 的（潜在）慢速操作不会阻塞服务器，实现高性能响应。

**多项目管理**：支持用户添加并管理多个独立的 `wg` 项目（文件夹）。

2. 🛠️ 技术选型
框架：FastAPI

理由： 用户首选。高性能（基于 asyncio），自动生成 API 文档 (Swagger UI)，拥有优秀的数据验证（Pydantic）。

服务器：uvicorn

理由： FastAPI 官方推荐的 ASGI 服务器。

wg 引擎交互：import（导入）

理由： 这是最重要的架构决策。我们不使用 subprocess 去调用 python3 wg.py ...，而是将 wg.py (V4.x) 重构为一个可导入的 Python 模块。

并发模型：asyncio.to_thread

理由： wg.py 的所有 run_command 函数本质上都是阻塞 I/O。我们必须在 FastAPI 的 async 事件循环之外的独立线程中运行它们，以防止整个服务器被“卡住”。

**项目持久化**: `projects.json`
理由: 使用一个简单的 JSON 文件来存储用户添加的项目路径列表，便于服务器重启后加载。

3. 📦 关键先决条件：重构 wg.py (V4.x -> V4.7+)
在构建 API 之前，wg.py 必须被重构为一个“库” (Library) 而不是一个“脚本”。

**使其可导入**： wg.py 中所有的 argparse 和 main() 逻辑必须被移动到 `if __name__ == "__main__":` 块中。

**支持多项目**:
*   所有 `handle_*` 函数（如 `handle_init`, `handle_status`, `handle_commit`）都必须接受一个新的**第一个参数 `project_path: str`**。
*   核心函数 `run_command` 必须接受 `cwd` 参数，并将其传递给 `subprocess.run(..., cwd=project_path)`，以确保所有 `git` 命令都在正确的项目目录中执行。

**函数返回数据**：
*   `handle_diff()`、`handle_status()`、`handle_log()` 必须停止 `print()`，而是**return** 它们获取到的数据（例如：diff 字符串、文件列表、日志条目列表）。
*   `handle_commit()`、`handle_restore()` 应该 `return True`（成功）或 `raise Exception`（失败），以便 API 可以捕获。
*   （重要）`handle_diff`：它必须捕获 `run_command` 的 `stdout`（标准输出）并 `return result.stdout`。

4. 🏗️ 构建逻辑与 API 端点 (Endpoints)
我们将创建一个 `main.py` 文件来运行 FastAPI 服务器。

4.1 Pydantic 模型 (数据验证)
我们需要为 API 的 request 和 response 定义清晰的数据结构。

Python

# main.py
from pydantic import BaseModel, Field
from typing import List, Optional

# (新增) 用于 'add project' 的请求体
class AddProjectRequest(BaseModel):
    path: str

# 用于 'commit' 的请求体
class CommitRequest(BaseModel):
    message: str
    files: Optional[List[str]] = Field(default_factory=list)

# 用于 'restore' 的请求体
class RestoreRequest(BaseModel):
    commit_id: str
    file_name: str # V4.x 只需要一个文件名

# 'status' 的响应体
class StatusFile(BaseModel):
    path: str
    status: str # 'M', 'A', '??'

# 'log' 的响应体
class LogEntry(BaseModel):
    id: str
    message: str
    author: str
    date: str

4.2 项目管理 API
这些端点用于管理用户项目列表。

`GET /api/projects`
*   **描述**: 获取已添加的所有项目的路径列表。
*   **实现**: 从 `projects.json` 文件读取路径列表并返回。
*   **响应**: `List[str]` (例如 `["/path/to/project1", "/path/to/project2"]`)

`POST /api/projects`
*   **描述**: 添加一个新的 `wg` 项目。
*   **请求体**: `AddProjectRequest`
*   **实现**:
    1.  接收 `{ path: "..." }`。
    2.  验证路径是否存在。
    3.  在**独立线程**中调用 `wg.handle_init(project_path=path)`，这会在该路径下初始化仓库。
    4.  将新路径追加到 `projects.json`。
    5.  返回成功或失败。

4.3 核心功能 API (项目特定)
这些是原有的 API，但现在**必须**通过查询参数 `project_path` 来指定操作目标。

Python

# main.py
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool # 兼容旧 Python
from fastapi.middleware.cors import CORSMiddleware # 允许 Vue 跨域访问

# 导入我们的“引擎”
# (假设重构后的 wg.py 就在旁边)
import wg 

app = FastAPI()

# --- 配置 CORS ---
# (允许 localhost:8080 (Vue) 访问 localhost:8000 (FastAPI))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"], # Vue 开发服务器的地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 关键：异步 I/O 包装器 ---
# FastAPI (async) 不能直接调用 wg.py (sync)
# 我们使用 run_in_threadpool (或 asyncio.to_thread) 
# 来在单独的线程中安全地运行阻塞函数

**所有核心功能 API 必须包含 `project_path` 查询参数**

@app.get("/api/status", response_model=List[StatusFile])
async def get_status(project_path: str, files: Optional[List[str]] = None):
    """
    获取指定项目的文件状态。
    """
    try:
        # 假设 wg.handle_status 被重构为接受 project_path
        status_list = await run_in_threadpool(
            wg.handle_status, 
            project_path, # <-- 新增
            files or []
        )
        return status_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diff/{file_name}")
async def get_diff(file_name: str, project_path: str):
    """
    获取单个文件的 diff。
    """
    try:
        # 假设 wg.handle_diff 被重构为接受 project_path
        diff_output = await run_in_threadpool(
            wg.handle_diff, 
            project_path, # <-- 新增
            [file_name]
        )
        return {"diff": diff_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commit")
async def do_commit(req: CommitRequest, project_path: str):
    """
    对指定项目执行提交。
    """
    try:
        # 假设 wg.handle_commit 被重构为接受 project_path
        success = await run_in_threadpool(
            wg.handle_commit, 
            project_path, # <-- 新增
            req.message, 
            req.files
        )
        if not success: # 假设“空提交”会返回 False
             return {"success": False, "message": "暂存区无变更，无需提交"}
        return {"success": True}
    except Exception as e:
        # 捕获 `git diff` 失败等错误
        raise HTTPException(status_code=500, detail=str(e))

# ... /api/log 和 /api/restore 端点 (逻辑类似, 同样需要 project_path) ...

# (用于 V5.1 WebSockets 的升级点)
# @app.websocket("/ws/status")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     # 在这里启动一个 'watchdog' 文件监视器
#     # ... 当 watchdog 检测到变化时:
#     #     await websocket.send_json({"update": True, "file": "Report.docx"})