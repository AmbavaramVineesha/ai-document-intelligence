import os
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import engine, Base, get_db
from backend.app.api.routes import health, documents
from backend.app.repositories.document_repository import DocumentRepository

# Create Database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths for static and templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Include API Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)

# Frontend Routes
@app.get("/", tags=["Frontend Dashboard"])
def render_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/view/{document_name}", tags=["Frontend Dashboard"])
def render_document_result(document_name: str, request: Request, db: Session = Depends(get_db)):
    repo = DocumentRepository(db)
    record = repo.get_by_document_name(document_name)
    payload = record.payload_json if record else None
    return templates.TemplateResponse(
        "document_result.html",
        {
            "request": request,
            "document_name": document_name,
            "document_found": record is not None,
            "data": payload
        }
    )
