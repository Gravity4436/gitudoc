import json
import asyncio
from typing import List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import our refactored engine
import wg

app = FastAPI(title="WG-Server", version="5.0")

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"], # Vue dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECTS_FILE = Path("projects.json")

# --- Pydantic Models ---

class AddProjectRequest(BaseModel):
    path: str

class CommitRequest(BaseModel):
    message: str
    files: Optional[List[str]] = Field(default_factory=list)

class RestoreRequest(BaseModel):
    commit_id: str
    file_name: str

class StatusFile(BaseModel):
    path: str
    status: str

class LogEntry(BaseModel):
    id: str
    message: str
    author: str
    date: str

# --- Helper Functions ---

def load_projects() -> List[str]:
    if not PROJECTS_FILE.exists():
        return []
    try:
        with open(PROJECTS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_projects(projects: List[str]):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects, f, indent=2)

# --- API Endpoints ---

@app.get("/api/projects", response_model=List[str])
async def get_projects():
    """Get list of all managed project paths."""
    return load_projects()

@app.post("/api/projects")
async def add_project(req: AddProjectRequest):
    """Add a new project and initialize it."""
    path_str = req.path
    abs_path = str(Path(req.path).resolve())
    if not Path(abs_path).exists():
        raise HTTPException(status_code=400, detail="Path does not exist")
    
    # Initialize (idempotent now)
    try:
        await run_in_threadpool(wg.handle_init, abs_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize project: {str(e)}")

    projects = load_projects()
    if abs_path not in projects:
        projects.append(abs_path)
        save_projects(projects)
    
    return {"message": "Project added", "path": abs_path}

@app.delete("/api/projects")
async def remove_project(path: str):
    """Remove a project from the list."""
    projects = load_projects()
    if path in projects:
        projects.remove(path)
        save_projects(projects)
    return {"success": True}

@app.post("/api/init")
async def init_project(project_path: str):
    """Ensure project is initialized (git init + pandoc config)."""
    try:
        await run_in_threadpool(wg.handle_init, project_path)
        return {"success": True}
    except Exception as e:
        print(f"Error in /api/init: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status", response_model=List[StatusFile])
async def get_status(project_path: str, files: Optional[List[str]] = Query(None)):
    """Get status of files in a project."""
    try:
        status_list = await run_in_threadpool(
            wg.handle_status, 
            project_path, 
            files or []
        )
        return status_list
    except Exception as e:
        print(f"Error in /api/status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diff/{file_name}")
async def get_diff(file_name: str, project_path: str):
    """Get diff for a specific file."""
    try:
        diff_output = await run_in_threadpool(
            wg.handle_diff, 
            project_path, 
            [file_name]
        )
        return {"diff": diff_output}
    except Exception as e:
        print(f"Error in /api/diff: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commit")
async def do_commit(req: CommitRequest, project_path: str):
    """Commit changes to a project."""
    try:
        success = await run_in_threadpool(
            wg.handle_commit, 
            project_path, 
            req.message, 
            req.files
        )
        if not success:
             return {"success": False, "message": "No changes to commit"}
        return {"success": True}
    except Exception as e:
        print(f"Error in /api/commit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/log", response_model=List[LogEntry])
async def get_log(project_path: str, files: Optional[List[str]] = Query(None)):
    """Get commit log for a project."""
    try:
        logs = await run_in_threadpool(
            wg.handle_log, 
            project_path, 
            files or []
        )
        return logs
    except Exception as e:
        print(f"Error in /api/log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/restore")
async def do_restore(req: RestoreRequest, project_path: str):
    """Restore a file to a previous version."""
    try:
        restored_path = await run_in_threadpool(
            wg.handle_restore, 
            project_path, 
            req.commit_id, 
            req.file_name
        )
        return {"success": True, "restored_path": restored_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ResetRequest(BaseModel):
    commit_id: str

@app.post("/api/reset")
async def do_reset(req: ResetRequest, project_path: str):
    """Reset project to a specific commit (Hard Reset)."""
    try:
        await run_in_threadpool(
            wg.handle_reset, 
            project_path, 
            req.commit_id
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/revert")
async def do_revert(req: ResetRequest, project_path: str): # Reusing ResetRequest as it only needs commit_id
    """Revert a specific commit."""
    try:
        await run_in_threadpool(
            wg.handle_revert_commit, 
            project_path, 
            req.commit_id
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
