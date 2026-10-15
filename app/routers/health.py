from fastapi import APIRouter, HTTPException

from app.core import db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    try:
        with db.pool().connection(timeout=2) as conn, conn.cursor() as cur:
            cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            row = cur.fetchone()
    except Exception as exc:
        raise HTTPException(503, f"база недоступна: {exc.__class__.__name__}") from exc
    if row is None:
        raise HTTPException(503, "расширение vector не активно")
    return {"status": "ok", "vector": row[0]}
