from abc import ABC, abstractmethod
import pickle
import uuid
import logging
import uvicorn.logging
from redis.asyncio import Redis
from sqlalchemy.orm import joinedload, Query
from sqlalchemy.orm.relationships import _RelationshipDeclared, RelationshipProperty
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
    """
    Concrete implementation of QueryExecutor with cache integration using Redis.

    This class inherits from both QueryExecutor and CacheableQuery, providing methods
    for fetching data from a database and invalidating corresponding cache entries
    using an asynchronous Redis client.
    """
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
        """
        Fetches all results from a query, using the cache if available.

        This method first attempts to retrieve the results from the cache using a
        generated key based on the query statement and parameters. If the cache
        misses, it fetches the data from the database using the provided query,
        adds joinedload options for efficient retrieval, and stores the results
        in the cache with the generated key and the configured TTL.

        Args:
            query (Query): The SQLAlchemy query object.
        Returns:
            List: The query results.
        """
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
        """
        Fetches the first result from a query, using the cache if available.

        This method first attempts to retrieve the result from the cache using a
        generated key based on the provided ID and query. If the cache misses,
        it fetches the data from the database using the provided query,
        adds joinedload options for efficient retrieval, and stores the result
        in the cache with the generated key and the configured TTL.

        Args:
            id_key (Any): The ID to use for generating the cache key.
            query (Query): The SQLAlchemy query object.
        Returns:
            Any: The first result from the query or None.
        """
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
        """
        Fetches a scalar value from a query, using the cache if available.

        This method first attempts to retrieve the scalar value from the cache using a
        generated key based on the provided ID and query. If the cache misses,
        it fetches the data from the database using the provided query,
        adds joinedload options for efficient retrieval, and stores the value
        in the cache with the generated key and the configured TTL.

        Args:
            id_key (Any): The ID to use for generating the cache key.
            query (Query): The SQLAlchemy query object.
        Returns:
            Any: The scalar value from the query.
        """
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
        """
        Invalidates all cached entries generated by `get_all`.

        This method iterates through all cache keys that match the prefix for
        cached results from `get_all` and deletes them from the cache.
        Raises:
            RuntimeError: If the Redis client is not configured.
        """
        if self.client:
            pattern = f"{self.all_prefix}*"
            async for cache_key in self.client.scan_iter(pattern):
                await self.client.delete(cache_key)
                logger.info(f"Redis Cache: record with {cache_key} invalidated")

    async def invalidate_cache_for_first(self, id_key):
        """Invalidates the cached entry generated by `get_first` for the provided ID.

        This method generates a cache key based on the provided ID and the prefix
        for cached results from `get_first`, and then deletes the corresponding
        entry from the cache.
        Raises:
            RuntimeError: If the Redis client is not configured.
        """
        if self.client:
            cache_key = CacheableQueryExecutor.__get_cache_key(prefix=self.first_prefix, key=id_key)
            await self.client.delete(cache_key)  
            logger.info(f"Redis Cache: record with {cache_key} invalidated")      
    
    async def invalidate_cache_for_scalar(self, id_key):
        """Invalidates the cached entry generated by `get_scalar` for the provided ID.

        This method generates a cache key based on the provided ID and the prefix
        for cached results from `get_scalar`, and then deletes the corresponding
        entry from the cache.
        Raises:
            RuntimeError: If the Redis client is not configured.
        """
        if self.client:
            cache_key = CacheableQueryExecutor.__get_cache_key(prefix=self.scalar_prefix, key=id_key)
            await self.client.delete(cache_key)  
            logger.info(f"Redis Cache: record with {cache_key} invalidated")      
    