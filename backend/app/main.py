from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.api.routes import health, documents

# Create Database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Build allowed origins list from config
allowed_origins = ["*"] if not settings.FRONTEND_URL else [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

# Enable CORS — allow configured frontend URL + local dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root path to interactive API documentation (/docs)."""
    return RedirectResponse(url="/docs")

# Include API Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)

