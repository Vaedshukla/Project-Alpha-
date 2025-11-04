from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes import auth, users, devices, browsing, blocked_sites, activity, reports


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # CORS
    allow_origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],
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

    @app.get("/health")
    async def health():
        return {"success": True, "message": "ok", "data": {"service": settings.app_name}}

    return app


app = create_app()

