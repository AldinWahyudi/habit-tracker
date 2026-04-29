from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import analytics, habits


def create_app() -> FastAPI:
    app = FastAPI(
        title="Habit Tracker API",
        version="0.1.0",
        description="Habit tracker with heatmaps, day-of-week analytics, "
        "Pearson correlations, and weekly Claude-powered insights.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    Base.metadata.create_all(bind=engine)

    app.include_router(habits.router)
    app.include_router(analytics.router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
