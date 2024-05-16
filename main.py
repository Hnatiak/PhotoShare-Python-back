import os
import re
from ipaddress import ip_address
from typing import Callable
from pathlib import Path

import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.routes import contacts, auth, users
from src.conf.config import config

app = FastAPI()

banned_ips = [
    ip_address("192.168.1.1"),
    ip_address("192.168.1.2"),
]

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

user_agent_ban_list = [r"Googlebot", r"Python-urllib"]

@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    print(request.headers.get("Authorization"))
    user_agent = request.headers.get("user-agent")
    print(user_agent)
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "You are banned"},
            )
    response = await call_next(request)
    return response

BASE_DIR = Path(__file__).parent
directory = BASE_DIR.joinpath("src").joinpath("static")
app.mount("/static", StaticFiles(directory=directory), name="static")

app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')

@app.on_event("startup")
async def startup():
    r = await redis.Redis(host=config.REDIS_DOMAIN, port=config.REDIS_PORT, db=0, password=config.REDIS_PASSWORD)
    await FastAPILimiter.init(r)

@app.get('/')
def index():
    return {"message": "Contact Application"}

@app.get("/api/healthchecker") # Декоратор який відповідає як побудувати документацію до проекту - перевіряє чи все добре спрацювало чи ні і який статус повернувся
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="База даних налаштована неправильно - зверніться до автора веб-сайту, тут не ваша помилка")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Помилка підключення до дата-бази - не вдалося, зверніться до автора веб-сайту, тут не ваша помилка")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(
        os.environ.get("PORT", 8000)), log_level="info")