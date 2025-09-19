from __future__ import annotations

import json
import sqlite3
import uuid
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

DB_PATH = "assistant_demo.db"

# -----------------------------
# Database setup and helpers
# -----------------------------

def init_db(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # responses table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS responses (
            response_id TEXT PRIMARY KEY,
            task_id TEXT,
            user_id TEXT,
            response_text TEXT,
            tone TEXT,
            status TEXT,
            timestamp TEXT
        )
        """
    )
    # embeddings table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            vector_blob TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            UNIQUE(item_type, item_id)
        )
        """
    )
    # coach_feedback table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS coach_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_id TEXT,
            task_id TEXT,
            response_id TEXT,
            score INTEGER,
            comment TEXT,
            timestamp TEXT
        )
        """
    )
    # metrics table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            status_code INTEGER,
            latency_ms REAL,
            timestamp TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def db_execute(query: str, params: Tuple[Any, ...] = ()) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()


def db_query_one(query: str, params: Tuple[Any, ...] = ()) -> Optional[tuple]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row


def db_query_all(query: str, params: Tuple[Any, ...] = ()) -> List[tuple]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


# -----------------------------
# Simple safety filter
# -----------------------------

BANNED_WORDS = {"badword", "unsafe"}


def check_safety(text: str) -> Tuple[bool, Optional[str]]:
    lower = text.lower()
    for w in BANNED_WORDS:
        if w in lower:
            return False, f"Contains banned word: {w}"
    return True, None


# -----------------------------
# Simple embedding and similarity
# -----------------------------

DIM = 64  # small dimensionality for speed


def text_to_vector(text: str, dim: int = DIM) -> List[float]:
    # Very lightweight hashing-based embedding
    vec = [0.0] * dim
    for token in text.split():
        h = hash(token)
        idx = h % dim
        vec[idx] += 1.0
    # L2 normalize
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = sum(a * a for a in v1) ** 0.5
    n2 = sum(b * b for b in v2) ** 0.5
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


def store_embedding(item_type: str, item_id: str, text: str) -> bool:
    try:
        vec = text_to_vector(text)
        blob = json.dumps(vec)
        ts = datetime.utcnow().isoformat()
        db_execute(
            """
            INSERT OR REPLACE INTO embeddings (item_type, item_id, vector_blob, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (item_type, item_id, blob, ts),
        )
        return True
    except Exception:
        return False


def get_embedding(item_type: str, item_id: str) -> Optional[List[float]]:
    row = db_query_one(
        "SELECT vector_blob FROM embeddings WHERE item_type=? AND item_id=?",
        (item_type, item_id),
    )
    if not row:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


def get_all_embeddings() -> List[Tuple[str, str, List[float]]]:
    rows = db_query_all("SELECT item_type, item_id, vector_blob FROM embeddings")
    out: List[Tuple[str, str, List[float]]] = []
    for itype, iid, blob in rows:
        try:
            out.append((itype, iid, json.loads(blob)))
        except Exception:
            continue
    return out


# -----------------------------
# Responder agent (lightweight)
# -----------------------------

def generate_response(task_id: str) -> Tuple[str, str]:
    # Simple deterministic response for demo
    text = f"Generated response for task {task_id}"
    tone = "polite"
    return text, tone


# -----------------------------
# FastAPI app and middleware
# -----------------------------

app = FastAPI(title="AI Assistant Unified API", version="1.0.0")


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        status_code: int = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
        finally:
            end = time.time()
            latency_ms = (end - start) * 1000.0
            path = request.url.path
            if not any(path.startswith(p) for p in ("/docs", "/openapi.json", "/favicon.ico")):
                try:
                    db_execute(
                        "INSERT INTO metrics (endpoint, status_code, latency_ms, timestamp) VALUES (?, ?, ?, ?)",
                        (path, status_code, float(latency_ms), datetime.utcnow().isoformat()),
                    )
                except Exception:
                    pass


@app.on_event("startup")
def _startup() -> None:
    init_db()


# -----------------------------
# Models
# -----------------------------

class RespondRequest(BaseModel):
    task_id: str
    user_id: Optional[str] = None
    task_text: Optional[str] = None


class RespondResponse(BaseModel):
    response_id: str
    task_id: str
    response_text: str
    tone: str
    status: str
    timestamp: str


class SearchSimilarRequest(BaseModel):
    summary_id: Optional[str] = None
    message_text: Optional[str] = None
    top_k: int = 3


class RelatedItem(BaseModel):
    item_type: str
    item_id: str
    score: float
    text: Optional[str] = None


class SearchSimilarResponse(BaseModel):
    related: List[RelatedItem]


class CoachFeedbackRequest(BaseModel):
    summary_id: str
    task_id: str
    response_id: str
    scores: Dict[str, int]
    comment: Optional[str] = None


class CoachFeedbackResponse(BaseModel):
    feedback_id: str
    score: int
    stored: bool


# -----------------------------
# Endpoints
# -----------------------------

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/respond", response_model=RespondResponse)
def api_respond(req: RespondRequest):
    text, tone = generate_response(req.task_id)
    ok, _ = check_safety(text)
    status = "ok" if ok else "flagged"

    response_id = "r" + uuid.uuid4().hex[:8]
    timestamp = datetime.utcnow().isoformat()

    db_execute(
        """
        INSERT INTO responses (response_id, task_id, user_id, response_text, tone, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (response_id, req.task_id, req.user_id or "u1", text, tone, status, timestamp),
    )

    return RespondResponse(
        response_id=response_id,
        task_id=req.task_id,
        response_text=text,
        tone=tone,
        status=status,
        timestamp=timestamp,
    )


@app.post("/api/search_similar", response_model=SearchSimilarResponse)
def api_search_similar(req: SearchSimilarRequest):
    if not req.summary_id and not req.message_text:
        raise HTTPException(status_code=400, detail="Either summary_id or message_text must be provided")

    query_vec: Optional[List[float]] = None
    if req.message_text:
        query_vec = text_to_vector(req.message_text)
    elif req.summary_id:
        ev = get_embedding("summary", req.summary_id)
        if ev is not None:
            query_vec = ev
        else:
            return SearchSimilarResponse(related=[])

    if query_vec is None:
        return SearchSimilarResponse(related=[])

    candidates = get_all_embeddings()
    scored: List[Tuple[str, str, float]] = []
    for item_type, item_id, vec in candidates:
        if req.summary_id and item_type == "summary" and item_id == req.summary_id:
            continue
        score = cosine_similarity(query_vec, vec)
        scored.append((item_type, item_id, score))

    scored.sort(key=lambda x: x[2], reverse=True)
    top = scored[: max(1, min(req.top_k, 10))]

    related = [RelatedItem(item_type=i, item_id=j, score=float(s), text=None) for i, j, s in top]
    return SearchSimilarResponse(related=related)


@app.post("/api/coach_feedback", response_model=CoachFeedbackResponse)
def api_coach_feedback(req: CoachFeedbackRequest):
    total_score = int(sum(int(v) for v in req.scores.values()))
    ts = datetime.utcnow().isoformat()

    db_execute(
        """
        INSERT INTO coach_feedback (summary_id, task_id, response_id, score, comment, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (req.summary_id, req.task_id, req.response_id, total_score, req.comment or "", ts),
    )

    row = db_query_one("SELECT MAX(id) FROM coach_feedback")
    feedback_id = f"f{row[0]}" if row and row[0] is not None else "f0"

    return CoachFeedbackResponse(feedback_id=feedback_id, score=total_score, stored=True)


@app.get("/api/metrics")
def api_metrics(hours: Optional[int] = None) -> Dict[str, Any]:
    rows = db_query_all("SELECT status_code, latency_ms FROM metrics")
    total_calls = len(rows)
    error_count = sum(1 for sc, _ in rows if sc is not None and int(sc) >= 400)
    avg_latency = (sum(float(lat) for _, lat in rows) / total_calls) if total_calls > 0 else 0.0
    error_rate = (error_count / total_calls) if total_calls > 0 else 0.0

    ep_rows = db_query_all("SELECT endpoint, COUNT(*), AVG(latency_ms) FROM metrics GROUP BY endpoint")
    endpoint_stats = [
        {"endpoint": ep, "calls": int(c), "avg_latency_ms": float(alat) if alat is not None else 0.0}
        for ep, c, alat in ep_rows
    ]

    row_resp = db_query_one("SELECT COUNT(*) FROM responses")
    total_responses = int(row_resp[0]) if row_resp and row_resp[0] is not None else 0

    return {
        "total_messages": 0,
        "total_summaries": 0,
        "total_tasks": 0,
        "total_responses": total_responses,
        "avg_latency_ms": avg_latency,
        "error_rate": error_rate,
        "endpoint_stats": endpoint_stats,
        "api_metrics": {
            "total_calls": total_calls,
            "error_count": error_count,
            "avg_latency_ms": avg_latency,
            "error_rate": error_rate,
        },
        "service_status": "active" if total_calls >= 0 else "unknown",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Optional: seed embeddings quickly for testing
@app.post("/api/store_embedding")
def api_store_embedding(item_type: str, item_id: str, text: str) -> Dict[str, Any]:
    ok = store_embedding(item_type, item_id, text)
    return {"stored": bool(ok)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
