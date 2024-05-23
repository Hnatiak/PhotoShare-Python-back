import base64
import uuid
import io
from sqlalchemy.orm import Session, Query
from src.entity.models import User, QRCode
from src.services.cache import QueryExecutor, CacheableQueryExecutor

class QRCodeRepository:
    def __init__(self, query_executor: QueryExecutor = None) -> None:
        self.query_executor = query_executor
    
    async def __first(self, id_key, query:Query):
        if self.query_executor:
            return await self.query_executor.get_first(id_key=id_key, query=query)
        return query.first()

    async def save_qrcode(self, photo_id: uuid.UUID, qr_code_binary: io.BytesIO, user: User, db: Session) -> QRCode:
        qr_code = QRCode(photo_id=photo_id, qr_code=base64.b64encode(qr_code_binary.getvalue()))
        db.add(qr_code)
        db.commit()
        db.refresh(qr_code)    
        return qr_code

    async def read_qrcode(self, photo_id: uuid.UUID, user: User, db: Session) -> io.BytesIO | None:
        query = db.query(QRCode).filter(QRCode.photo_id == photo_id)
        qr_code = await self.__first(id_key=photo_id, query=query)    
        qr_stream = None 
        if qr_code:
            qr_stream = io.BytesIO(base64.b64decode(qr_code.qr_code))
            qr_stream.seek(0)
        return qr_stream


repository_qrcode = QRCodeRepository(query_executor=CacheableQueryExecutor())
