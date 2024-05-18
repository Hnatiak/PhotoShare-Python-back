import base64
import uuid
import io
from typing import List
from sqlalchemy import func, and_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.relationships import _RelationshipDeclared
from sqlalchemy.orm.properties import ColumnProperty
from fastapi import UploadFile
from src.entity.models import Photo, Tag, User, AssetType, QRCode
from datetime import datetime, timedelta
from src.schemas.schemas import PhotoBase, PhotoResponse

async def save_qr_code(photo_id: uuid.UUID, qr_code_binary: io.BytesIO, user: User, db: Session) -> None:
    qr_code = QRCode(photo_id=photo_id, qr_code=base64.b64encode(qr_code_binary.getvalue()))
    db.add(qr_code)
    db.commit()
    db.refresh(qr_code)    
    return bool(qr_code)

async def read_qr_code(photo_id: uuid.UUID, user: User, db: Session) -> io.BytesIO | None:
    qr_code = db.query(QRCode).filter(QRCode.photo_id == photo_id).first()    
    qr_stream = None 
    if qr_code:
        qr_stream = io.BytesIO(base64.b64decode(qr_code.qr_code))
        qr_stream.seek(0)
    return qr_stream
