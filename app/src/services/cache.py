from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import pickle
import uuid
import logging
import uvicorn.logging
from redis.asyncio import Redis
from typing import Hashable, List
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload, Query
from sqlalchemy.orm.relationships import _RelationshipDeclared, RelationshipProperty
from src.entity.models import Base
from src.database.db import redis_client_async


logger = logging.getLogger(uvicorn.logging.__name__)


class ArgsUnhashable(Exception):
    pass

class QueryExecutor (ABC):
    @abstractmethod
    async def get_all(self, query: Query):
        pass

    @abstractmethod
    async def get_first(self, id_key, query: Query):
        pass
    
    @abstractmethod
    async def get_scalar(self, id_key, query: Query):
        pass

class CacheableQuery(ABC):
    @abstractmethod
    async def invalidate_cache_for_all(self):
        pass

    @abstractmethod
    async def invalidate_cache_for_first(self, id_key):
        pass
    
    @abstractmethod
    async def invalidate_cache_for_scalar(self, id_key):
        pass

class CacheableQueryExecutor(QueryExecutor, CacheableQuery):
    def __init__(self, ttl: int = None) -> None:
        self.client = redis_client_async
        self.ttl = ttl or 15*60
        self.prefix = id(self)
        self.all_prefix = f"{self.prefix}_all_"
        self.first_prefix = f"{self.prefix}_first_"
        self.scalar_prefix = f"{self.prefix}_scalar_"

    @classmethod
    def __get_cache_key(cls, prefix, key):
        try:
            cache_key = hash(key)
            return f"{prefix}{cache_key}"     
        except TypeError:
            raise ArgsUnhashable() 
    
    async def __getitem__(self, key):
        if not await self.client.exists(key):
            raise KeyError()
        else:
            result = await self.client.get(key)
            return pickle.loads(result)

    async def _set(self, key, value, ttl=None):
        value = pickle.dumps(value)
        await self.client.set(key, value)
        await self.client.expire(key, ttl)        

    async def _get(self, key, default=None):
        """
        Fetch a given key from the cache. If the key does not exist, return
        default, which itself defaults to None.
        """

        try:
            return await self[key]
        except KeyError:
            return default

    async def __get_all(self, query: Query):
        return query.all()
    
    async def __get_first(self, query: Query):
        return query.first()
    
    async def __get_scalar(self, query: Query):
        return query.scalar()

    def __add_joinedload(self, query: Query) -> Query:
        options = []       
        entity_type = query._propagate_attrs['plugin_subject'].class_
        for name, value in entity_type.__dict__.items():
            if hasattr(value, 'property') and (isinstance(value.property, _RelationshipDeclared) or isinstance(value.property, RelationshipProperty)):
                options.append(joinedload(getattr(entity_type, name)))                
        return query.options(*options)

    async def get_all(self, query: Query):
        if not self.client:
            return await self.__get_all(query=query)
        try:
            statement = query.statement.compile()
            cache_key = CacheableQueryExecutor.__get_cache_key(prefix=self.all_prefix, key = (str(statement), str(statement.params)))   
            value = await self._get(cache_key)
            if not value:          
                logger.info(f"Redis Cache: MISS - no record for {cache_key} found")
                query = self.__add_joinedload(query)
                value = await self.__get_all(query=query)
                if value:
                    await self._set(cache_key, value, self.ttl)
                    logger.info(f"Redis Cache: NEW RECORD with {cache_key} added") 
            else: 
                logger.info(f"Redis Cache: SUCCESS - record for {cache_key} found")  
            return value            
        except ArgsUnhashable:
            return await self.__get_all(query=query)

    async def get_first(self, id_key, query: Query):
        if not self.client:
            return await self.__get_first(query=query)
        try:
            cache_key = CacheableQueryExecutor.__get_cache_key(prefix=self.first_prefix, key=id_key)            
            value = await self._get(cache_key)
            if not value:
                logger.info(f"Redis Cache: MISS - no record for {cache_key} found")                
                query = self.__add_joinedload(query)
                value = await self.__get_first(query=query)
                if value:
                    await self._set(cache_key, value, self.ttl)
                    logger.info(f"Redis Cache: NEW RECORD with {cache_key} added")
            else: 
                logger.info(f"Redis Cache: SUCCESS - record for {cache_key} found")  
            return value            
        except ArgsUnhashable:
            return await self.__get_first(query=query)
    
    async def get_scalar(self, id_key, query: Query):
        if not self.client:
            return await self.__get_scalar(query=query)
        try:
            cache_key = CacheableQueryExecutor.__get_cache_key(prefix=self.scalar_prefix, key=id_key)            
            value = await self._get(cache_key)
            if not value:
                logger.info(f"Redis Cache: MISS - no record for {cache_key} found")                
                query = self.__add_joinedload(query)
                value = await self.__get_scalar(query=query)
                if value:
                    await self._set(cache_key, value, self.ttl)
                    logger.info(f"Redis Cache: NEW RECORD with {cache_key} added")
            else: 
                logger.info(f"Redis Cache: SUCCESS - record for {cache_key} found")  
            return value            
        except ArgsUnhashable:
            return await self.__get_scalar(query=query)   
        
    async def invalidate_cache_for_all(self):
        if self.client:
            pattern = f"{self.all_prefix}*"
            async for cache_key in self.client.scan_iter(pattern):
                await self.client.delete(cache_key)
                logger.info(f"Redis Cache: record with {cache_key} invalidated")

    async def invalidate_cache_for_first(self, id_key):
        if self.client:
            cache_key = CacheableQueryExecutor.__get_cache_key(prefix=self.first_prefix, key=id_key)
            await self.client.delete(cache_key)  
            logger.info(f"Redis Cache: record with {cache_key} invalidated")      
    
    async def invalidate_cache_for_scalar(self, id_key):
        if self.client:
            cache_key = CacheableQueryExecutor.__get_cache_key(prefix=self.scalar_prefix, key=id_key)
            await self.client.delete(cache_key)  
            logger.info(f"Redis Cache: record with {cache_key} invalidated")      
    