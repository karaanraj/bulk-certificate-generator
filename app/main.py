from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.db.database import Base, engine
from app.services.storage import ensure_storage_dirs

Base.metadata.create_all(bind=engine)
ensure_storage_dirs()

app = FastAPI(
    title="Bulk Certificate Generator",
    version="1.0.0",
    description="Generate and track certificates for bulk recipient lists.",
)

app.include_router(router, prefix="/api")

app.mount("/generated", StaticFiles(directory="storage/generated"), name="generated")
