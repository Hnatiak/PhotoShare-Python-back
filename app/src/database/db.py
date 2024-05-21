import redis
import redis.asyncio as redis_async
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.conf.config import settings


SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url
engine = create_engine(SQLALCHEMY_DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

redis_client_async = redis_async.Redis(host=settings.redis_host, 
                        port=settings.redis_port, 
                        db=0, encoding="utf-8",
                        decode_responses=True
                        )

redis_client = redis.StrictRedis(host=settings.redis_host, 
                        port=settings.redis_port)
# Dependency
def get_db():
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
