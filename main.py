# main.py

from fastapi import FastAPI, Request, Response
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.database import init_db
from src.controllers.contacts import router
from src.controllers.auth import router as auth_router

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.utils.limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    lifespan=lifespan,  
    default_response_class=ORJSONResponse, 
    title="Contacts API", 
    description="API for managing contacts with authentication and email notifications", 
    version="1.0.0"
)

app.state.limiter = limiter

def rate_limit_custom_handler(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, RateLimitExceeded)
    return _rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, rate_limit_custom_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)

def main():
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()