from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes import auth, users, devices, browsing, blocked_sites, activity, reports, agent

from app.routes import policy
from app.routes import dev

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # CORS

    app.add_middleware(
    CORSMiddleware,
#    allow_origins=["http://localhost:3000"],
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


    # Mount routers under API prefix
    prefix = settings.api_prefix
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(devices.router, prefix=prefix)
    app.include_router(browsing.router, prefix=prefix)
    app.include_router(blocked_sites.router, prefix=prefix)
    app.include_router(activity.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)
    app.include_router(agent.router, prefix=prefix)
    app.include_router(policy.router, prefix=prefix)
    app.include_router(dev.router, prefix=settings.api_prefix)
    
    @app.get("/health")
    async def health():
        return {"success": True, "message": "ok", "data": {"service": settings.app_name}}

    return app


app = create_app()
