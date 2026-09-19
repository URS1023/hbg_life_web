from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .providers import generate_plan


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("HBG_DATA_DIR", ROOT / ".runtime"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.getenv("HBG_DB_PATH", DATA_DIR / "studio.sqlite3"))
MEDIA_DIR = DATA_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
DB_LOCK = threading.RLock()
TASKS: dict[str, asyncio.Task[None]] = {}
TASK_MODE = os.getenv("HBG_TASK_MODE", "direct")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with DB_LOCK, db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY,
              email TEXT NOT NULL UNIQUE,
              name TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS projects (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              title TEXT NOT NULL,
              input_mode TEXT NOT NULL,
              orientation TEXT NOT NULL,
              step TEXT NOT NULL DEFAULT 'input',
              status TEXT NOT NULL DEFAULT 'draft',
              source_text TEXT NOT NULL DEFAULT '',
              script_text TEXT NOT NULL DEFAULT '',
              brief_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
              project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
              kind TEXT NOT NULL,
              status TEXT NOT NULL,
              progress INTEGER NOT NULL DEFAULT 0,
              message TEXT NOT NULL DEFAULT '',
              result_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id, updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_jobs_project ON jobs(project_id, created_at DESC);
            """
        )
        seed = conn.execute("SELECT id FROM users LIMIT 1").fetchone()
        if not seed:
            conn.execute(
                "INSERT INTO users(id,email,name,created_at) VALUES (?,?,?,?)",
                ("demo-user", "demo@hbg.local", "演示创作者", utc_now()),
            )
        conn.commit()


init_db()


class UserOut(BaseModel):
    id: str
    email: str
    name: str


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    input_mode: Literal["keyword", "script"] = "keyword"
    orientation: Literal["landscape", "portrait"] = "landscape"
    source_text: str = Field(default="", max_length=50_000)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    step: str | None = None
    source_text: str | None = Field(default=None, max_length=50_000)
    script_text: str | None = Field(default=None, max_length=100_000)
    brief: dict[str, Any] | None = None


class JobCreate(BaseModel):
    kind: Literal["plan", "storyboard", "narration", "images", "render"]


def current_user(authorization: str | None = Header(default=None)) -> sqlite3.Row:
    # Local development auth intentionally uses a deterministic demo session. Replace with OAuth/JWT in M1 auth hardening.
    user_id = "demo-user"
    if authorization and authorization.startswith("Bearer "):
        user_id = authorization.removeprefix("Bearer ").strip() or user_id
    with DB_LOCK, db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户会话无效")
    return user


def project_row(project_id: str, user_id: str) -> sqlite3.Row:
    with DB_LOCK, db() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id=? AND user_id=?", (project_id, user_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="项目不存在或无权访问")
    return row


def project_payload(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"], "title": row["title"], "inputMode": row["input_mode"],
        "orientation": row["orientation"], "step": row["step"], "status": row["status"],
        "sourceText": row["source_text"], "scriptText": row["script_text"],
        "brief": json.loads(row["brief_json"] or "{}"),
        "createdAt": row["created_at"], "updatedAt": row["updated_at"],
    }


def job_payload(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"], "projectId": row["project_id"], "kind": row["kind"],
        "status": row["status"], "progress": row["progress"], "message": row["message"],
        "result": json.loads(row["result_json"] or "{}"),
        "createdAt": row["created_at"], "updatedAt": row["updated_at"],
    }


def update_job(job_id: str, **values: Any) -> None:
    values["updated_at"] = utc_now()
    columns = ", ".join(f"{key}=?" for key in values)
    with DB_LOCK, db() as conn:
        conn.execute(f"UPDATE jobs SET {columns} WHERE id=?", (*values.values(), job_id))
        conn.commit()


async def run_job(job_id: str, user_id: str, project_id: str, kind: str) -> None:
    stages = {
        "plan": [
            (18, "分析创作意图与受众"), (42, "生成故事方向与章节"),
            (70, "整理旁白稿"), (100, "故事规划已完成"),
        ],
        "storyboard": [(24, "提取语义节拍"), (58, "规划角色和场景"), (84, "生成镜头提示词"), (100, "分镜已完成")],
        "narration": [(30, "准备旁白文本"), (68, "生成语音和字幕时间"), (100, "旁白已完成")],
        "images": [(20, "准备角色锚点"), (55, "生成镜头候选图"), (86, "检查图片尺寸与可读性"), (100, "图片生成已完成")],
        "render": [(12, "检查素材与时间轴"), (44, "渲染镜头"), (76, "混合旁白与配乐"), (92, "执行成片质检"), (100, "成片已完成")],
    }
    try:
        for progress, message in stages[kind]:
            await asyncio.sleep(0.45)
            with DB_LOCK, db() as conn:
                current = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not current or current["status"] == "cancelled":
                return
            update_job(job_id, progress=progress, message=message, status="running")
        result: dict[str, Any] = {"mode": "local-demo", "kind": kind}
        if kind == "plan":
            with DB_LOCK, db() as conn:
                source_row = conn.execute("SELECT source_text, input_mode FROM projects WHERE id=? AND user_id=?", (project_id, user_id)).fetchone()
            result["brief"], result["mode"] = await asyncio.to_thread(generate_plan, source_row["source_text"], source_row["input_mode"])
            with DB_LOCK, db() as conn:
                conn.execute("UPDATE projects SET brief_json=?, script_text=?, step='planning', updated_at=? WHERE id=? AND user_id=?", (json.dumps(result["brief"], ensure_ascii=False), "今天体验的人生副本是。\n\n第一章：进入副本\n\n这是一个可以继续编辑的旁白草稿。", utc_now(), project_id, user_id))
                conn.commit()
        if kind == "storyboard":
            shots = [
                {"id": "shot-01", "cue": "进入副本", "visual": "主角站在清晨的县城街口，手里握着一张尚未打开的车票。", "motion": "zoom-in", "prompt": "HBG 漫画风，统一主角身份锚点，清晨县城街口，电影感广角构图，暖灰色调，无文字"},
                {"id": "shot-02", "cue": "第一次选择", "visual": "主角在外卖电动车与旧书桌之间犹豫，窗外开始下雨。", "motion": "pan-left", "prompt": "HBG 漫画风，统一主角身份锚点，室内旧书桌与电动车并置，雨天侧光，中景构图，无额外人物"},
                {"id": "shot-03", "cue": "代价与转折", "visual": "夜里主角在便利店门口抬头，霓虹倒映在积水里。", "motion": "zoom-out", "prompt": "HBG 漫画风，统一主角身份锚点，夜晚便利店门口，霓虹积水倒影，低机位情绪镜头，无文字"},
                {"id": "shot-04", "cue": "新的答案", "visual": "主角推开工作室的门，第一束阳光落在桌面上。", "motion": "hold", "prompt": "HBG 漫画风，统一主角身份锚点，工作室门口逆光，温暖希望氛围，远景构图，无额外人物"},
            ]
            with DB_LOCK, db() as conn:
                row = conn.execute("SELECT brief_json FROM projects WHERE id=? AND user_id=?", (project_id, user_id)).fetchone()
                brief = json.loads(row["brief_json"] or "{}")
                brief["shots"] = shots
                conn.execute("UPDATE projects SET brief_json=?, updated_at=? WHERE id=? AND user_id=?", (json.dumps(brief, ensure_ascii=False), utc_now(), project_id, user_id))
                conn.commit()
            result["shots"] = shots
        if kind == "narration":
            with DB_LOCK, db() as conn:
                row = conn.execute("SELECT brief_json, script_text FROM projects WHERE id=? AND user_id=?", (project_id, user_id)).fetchone()
                brief = json.loads(row["brief_json"] or "{}")
                duration = round(max(8, len(row["script_text"]) / 4.0), 1)
                brief["narration"] = {"duration": duration, "voice": "zh-CN-YunjianNeural (演示)"}
                conn.execute("UPDATE projects SET brief_json=?, updated_at=? WHERE id=? AND user_id=?", (json.dumps(brief, ensure_ascii=False), utc_now(), project_id, user_id))
                conn.commit()
            result["narration"] = brief["narration"]
        if kind == "images":
            with DB_LOCK, db() as conn:
                row = conn.execute("SELECT brief_json FROM projects WHERE id=? AND user_id=?", (project_id, user_id)).fetchone()
                brief = json.loads(row["brief_json"] or "{}")
                count = len(brief.get("shots", [])) or 4
                brief["images"] = {"count": count, "selected": count}
                conn.execute("UPDATE projects SET brief_json=?, updated_at=? WHERE id=? AND user_id=?", (json.dumps(brief, ensure_ascii=False), utc_now(), project_id, user_id))
                conn.commit()
            result["images"] = brief["images"]
        if kind == "render":
            video_path = MEDIA_DIR / project_id / "preview.mp4"
            video_path.parent.mkdir(parents=True, exist_ok=True)
            title = project_row(project_id, user_id)["title"]
            # The first vertical slice uses a deterministic local slate. The same job boundary
            # is where the production renderer will invoke the existing HBG composition scripts.
            safe_title = title.replace("'", "")[:38]
            drawtext = f"drawtext=text='{safe_title}':fontcolor=white:fontsize=42:x=(w-text_w)/2:y=(h-text_h)/2"
            await asyncio.to_thread(
                subprocess.run,
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x182337:s=1280x720:r=30", "-vf", drawtext, "-t", "4", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-an", str(video_path)],
                check=True,
            )
            result["videoUrl"] = f"/api/projects/{project_id}/preview"
            result["fileName"] = video_path.name
            with DB_LOCK, db() as conn:
                conn.execute("UPDATE projects SET status='ready', step='export', updated_at=? WHERE id=? AND user_id=?", (utc_now(), project_id, user_id))
                conn.commit()
        else:
            next_step = {"plan": "planning", "storyboard": "storyboard", "narration": "narration", "images": "images"}.get(kind)
            if next_step:
                with DB_LOCK, db() as conn:
                    conn.execute("UPDATE projects SET step=?, updated_at=? WHERE id=? AND user_id=?", (next_step, utc_now(), project_id, user_id))
                    conn.commit()
        update_job(job_id, status="succeeded", progress=100, message=stages[kind][-1][1], result_json=json.dumps(result, ensure_ascii=False))
    except asyncio.CancelledError:
        update_job(job_id, status="cancelled", message="任务已取消")
        raise
    except Exception as exc:  # pragma: no cover - defensive boundary
        update_job(job_id, status="failed", message=f"任务失败：{exc}")
    finally:
        TASKS.pop(job_id, None)


app = FastAPI(title="HBG Life Studio API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "database": str(DB_PATH), "mode": "local-demo"}


@app.get("/api/me", response_model=UserOut)
def me(user: sqlite3.Row = Depends(current_user)) -> UserOut:
    return UserOut(id=user["id"], email=user["email"], name=user["name"])


@app.get("/api/projects")
def list_projects(user: sqlite3.Row = Depends(current_user)) -> list[dict[str, Any]]:
    with DB_LOCK, db() as conn:
        rows = conn.execute("SELECT * FROM projects WHERE user_id=? ORDER BY updated_at DESC", (user["id"],)).fetchall()
    return [project_payload(row) for row in rows]


@app.post("/api/projects", status_code=201)
def create_project(payload: ProjectCreate, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    project_id, now = str(uuid.uuid4()), utc_now()
    with DB_LOCK, db() as conn:
        conn.execute("INSERT INTO projects(id,user_id,title,input_mode,orientation,source_text,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)", (project_id, user["id"], payload.title, payload.input_mode, payload.orientation, payload.source_text, now, now))
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    return project_payload(row)


@app.get("/api/projects/{project_id}")
def get_project(project_id: str, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    return project_payload(project_row(project_id, user["id"]))


@app.patch("/api/projects/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    project_row(project_id, user["id"])
    fields: dict[str, Any] = {"updated_at": utc_now()}
    if payload.title is not None: fields["title"] = payload.title
    if payload.step is not None: fields["step"] = payload.step
    if payload.source_text is not None: fields["source_text"] = payload.source_text
    if payload.script_text is not None: fields["script_text"] = payload.script_text
    if payload.brief is not None: fields["brief_json"] = json.dumps(payload.brief, ensure_ascii=False)
    with DB_LOCK, db() as conn:
        columns = ", ".join(f"{key}=?" for key in fields)
        conn.execute(f"UPDATE projects SET {columns} WHERE id=? AND user_id=?", (*fields.values(), project_id, user["id"]))
        conn.commit()
    return project_payload(project_row(project_id, user["id"]))


@app.get("/api/projects/{project_id}/jobs")
def list_jobs(project_id: str, user: sqlite3.Row = Depends(current_user)) -> list[dict[str, Any]]:
    project_row(project_id, user["id"])
    with DB_LOCK, db() as conn:
        rows = conn.execute("SELECT * FROM jobs WHERE project_id=? AND user_id=? ORDER BY created_at DESC", (project_id, user["id"])).fetchall()
    return [job_payload(row) for row in rows]


@app.post("/api/projects/{project_id}/jobs", status_code=202)
async def create_job(project_id: str, payload: JobCreate, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    project_row(project_id, user["id"])
    job_id, now = str(uuid.uuid4()), utc_now()
    with DB_LOCK, db() as conn:
        conn.execute("INSERT INTO jobs(id,user_id,project_id,kind,status,message,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)", (job_id, user["id"], project_id, payload.kind, "queued", "排队中", now, now))
        conn.commit()
    if TASK_MODE == "direct":
        TASKS[job_id] = asyncio.create_task(run_job(job_id, user["id"], project_id, payload.kind))
    with DB_LOCK, db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return job_payload(row)


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    with DB_LOCK, db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=? AND user_id=?", (job_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="任务不存在")
    if row["status"] in {"succeeded", "failed", "cancelled"}:
        return job_payload(row)
    task = TASKS.get(job_id)
    if task:
        task.cancel()
    update_job(job_id, status="cancelled", message="已取消")
    with DB_LOCK, db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return job_payload(row)


@app.get("/api/projects/{project_id}/preview")
def preview(project_id: str, user: sqlite3.Row = Depends(current_user)) -> Any:
    project = project_row(project_id, user["id"])
    video_path = MEDIA_DIR / project_id / "preview.mp4"
    if video_path.exists() and project["status"] == "ready":
        return FileResponse(video_path, media_type="video/mp4", filename=f"{project['title']}.mp4")
    return {"projectId": project_id, "status": project["status"], "message": "视频尚未完成渲染", "mode": "local-demo"}
