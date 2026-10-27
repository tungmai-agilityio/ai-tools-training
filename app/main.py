from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import auth, config
from app.auth_routes import router as auth_router
from app.errors import DomainError
from app.routes import router
from app.users import router as users_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    auth.seed_admin()
    yield


app = FastAPI(title="Clinic Booking", lifespan=lifespan)
app.include_router(router)
app.include_router(auth_router)
app.include_router(users_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.exception_handler(RequestValidationError)
def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Default 422 body, minus `input` and `ctx`: a rejected password must never be echoed back."""
    detail = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(DomainError)
def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"detail": exc.message})


@app.get("/health")
def health():
    """Liveness / readiness probe returning the service status and configured timezone."""
    return {"status": "ok", "timezone": config.CLINIC_TIMEZONE}


DOCS_PATHS = {"/docs", "/redoc", "/docs/oauth2-redirect"}  # Swagger needs a CDN script and an inline one
CSP = "script-src 'self'; object-src 'none'; base-uri 'self'"
UNSAFE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """CSP on every response; refuse unsafe requests from another origin (second layer behind SameSite=Strict)."""
    origin = request.headers.get("origin")
    if request.method in UNSAFE_METHODS and origin and urlsplit(origin).netloc != request.headers.get("host"):
        response = JSONResponse(status_code=403, content={"detail": "Cross-origin request refused"})
    else:
        response = await call_next(request)
    if request.url.path not in DOCS_PATHS:
        response.headers["Content-Security-Policy"] = CSP
    return response
