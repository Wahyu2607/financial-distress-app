from __future__ import annotations

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from backend.config import settings
from backend.database import init_database
from backend.routers import auth_router, users_router, admin_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Sistem Backend Autentikasi, Otorisasi RBAC, dan Validasi Email",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Konfigurasi CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pada produksi, sesuaikan dengan domain frontend resmi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)


# ==============================================================================
# STANDARISASI PENANGANAN ERROR (GLOBAL EXCEPTION HANDLERS)
# Format respons konsisten sesuai spesifikasi: { success: false, message: ..., error: ... }
# ==============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Menangani seluruh HTTPException dengan format JSON standar."""
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code", "HTTP_ERROR")
        msg = detail.get("message", "Terjadi kesalahan pada permintaan Anda.")
        extra = {k: v for k, v in detail.items() if k not in ("code", "message")}
    else:
        code = "HTTP_ERROR"
        msg = str(detail)
        extra = None

    content = {
        "success": False,
        "message": msg,
        "error": {
            "code": code,
        }
    }
    if extra:
        content["error"]["details"] = extra

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=getattr(exc, "headers", None)
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Menangani error validasi payload Pydantic dengan format 422 standar."""
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors.append(f"{loc}: {err.get('msg', 'Input tidak valid')}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validasi data masukan gagal",
            "error": {
                "code": "VALIDATION_ERROR",
                "details": errors
            }
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Menangani unhandled internal server error tanpa membocorkan stack trace database."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Terjadi kesalahan internal pada server. Silakan hubungi tim teknis.",
            "error": {
                "code": "INTERNAL_SERVER_ERROR"
            }
        }
    )


@app.on_event("startup")
def on_startup():
    """Inisialisasi tabel database saat aplikasi FastAPI berjalan."""
    init_database()


@app.get("/health", tags=["Monitoring"])
def health_check():
    """Pemeriksaan status kesehatan service backend."""
    return {
        "success": True,
        "message": "Service autentikasi backend beroperasi normal",
        "data": {
            "app": settings.APP_NAME,
            "env": settings.APP_ENV,
            "status": "healthy"
        }
    }
