import os
import signal
import uvicorn
import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager

import uvicorn.logging
import redis.asyncio as redis

from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware
from src.conf.config import settings
from src.database.db import engine
from src.routes import auth, comments

logger = logging.getLogger(uvicorn.logging.__name__)

origins = settings.cors_origins.split('|')


@asynccontextmanager
async def lifespan(_):
    #startup initialization goes here
    logger.info("Knock-knock...")
    logger.info("Uvicorn has you...")
    r = await redis.Redis(host=settings.redis_host, 
                          port=settings.redis_port, 
                          db=0, encoding="utf-8",
                          decode_responses=True
                          )
    await FastAPILimiter.init(r)
    yield
    #shutdown logic goes here    
    engine.dispose()
    await r.close(True)
    await FastAPILimiter.close()
    logger.info("Good bye, Mr. Anderson")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix='/api')
app.include_router(comments.router, prefix='/api')

@app.get("/")
def read_root():
    return {"message": "Wake up!"}
    

if __name__ == '__main__':
    try:
        uvicorn.run("main:app", host='0.0.0.0', port=8000, reload=True)
    except KeyboardInterrupt:
        os.kill(os.getpid(), signal.SIGBREAK)
