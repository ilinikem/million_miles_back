from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import million_mile

app = FastAPI(title="Million miles Service")


# Обработчик ошибок 404 и 502
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(
        request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"detail": "Ресурс не найден. Проверьте URL."},
        )
    elif exc.status_code == 502:
        return JSONResponse(
            status_code=502,
            content={"detail": "Ошибка шлюза: внешний сервис недоступен."},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

app.include_router(million_mile.router)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"^(https://million_miles\.ru|http://localhost:3000)$"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
