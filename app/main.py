import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Standalone service — no monolithic sys.path needed

from .ui_router import router as ui_router

# Single service entrypoint
app = FastAPI(
    title="RG Users Invariants SIM Service",
    description="User-facing Hash Sphere state-space invariants and physics simulation for Genesis2026",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rg_users_invarients_sim"}

# Root endpoint
@app.get("/")
async def root():
    frontend_path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(str(frontend_path))
    return JSONResponse({"message": "Users Invariants SIM frontend not found"}, status_code=404)

# Service-specific endpoint
@app.get("/api/v1/status")
async def status():
    return {"service": "rg_users_invarients_sim", "status": "active", "version": "1.0.0"}


# UI / Visualizer API (served at /api/*)
app.include_router(ui_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)
