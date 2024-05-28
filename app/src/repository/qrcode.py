import base64
import uuid
import io
from sqlalchemy.orm import Session, Query
from src.entity.models import User, QRCode
from src.services.cache import QueryExecutor, CacheableQueryExecutor

class QRCodeRepository:
    """
    Provides data access operations for QRCode entities.

    This class is responsible for interacting with the database to perform CRUD (Create, Read)
    operations on QRCode records associated with photos. It leverages a query executor
    for potential caching of queries.
    """
    def __init__(self, query_executor: QueryExecutor = None) -> None:
        self.query_executor = query_executor
    
    async def __first(self, id_key, query:Query):
        """
        Executes the provided SQLAlchemy query and fetches the first result.

        Args:
            id_key: The key to use for identifying the first record (e.g., primary key)
            query (Query): The SQLAlchemy query to be executed.
        Returns:
            QRCode: A QRCode object representing the first record in the query results, or None if no results are found.
        """
        if self.query_executor:
            return await self.query_executor.get_first(id_key=id_key, query=query)
        return query.first()

    async def save_qrcode(self, photo_id: uuid.UUID, qr_code_binary: io.BytesIO, user: User, db: Session) -> QRCode:
        """
        Saves a QR code binary representation associated with a specific photo.

        This method takes a photo ID, a BytesIO object containing the QR code binary data,
        and a User object representing the owner. It creates a new QRCode record in the database
        storing the base64 encoded QR code data linked to the provided photo ID.

        Args:
            photo_id (uuid.UUID): The unique identifier of the photo associated with the QR code.
            qr_code_binary (io.BytesIO): A BytesIO object containing the QR code binary data.
            user (User): The User object representing the owner of the photo and QR code.
            db (Session): The database session object.
        Returns:
            QRCode: A QRCode object representing the newly created record.
        """
        qr_code = QRCode(photo_id=photo_id, qr_code=base64.b64encode(qr_code_binary.getvalue()))
        db.add(qr_code)
        db.commit()
        db.refresh(qr_code)    
        return qr_code

    async def read_qrcode(self, photo_id: uuid.UUID, user: User, db: Session) -> io.BytesIO | None:
        """
        Retrieves the QR code binary data associated with a specific photo.

        This method takes a photo ID and fetches the corresponding QRCode record from the database.
        If a record exists, the method decodes the base64 encoded QR code data and returns a BytesIO
        object containing the binary representation.

        Args:
            photo_id (uuid.UUID): The unique identifier of the photo associated with the QR code.
            user (User): The User object representing the owner of the photo and QR code.
            db (Session): The database session object.
        Returns:
            io.BytesIO | None: A BytesIO object containing the QR code binary data if found, or None if no QR code is associated with the photo.
        """
        query = db.query(QRCode).filter(QRCode.photo_id == photo_id)
        qr_code = await self.__first(id_key=photo_id, query=query)    
        qr_stream = None 
        if qr_code:
            qr_stream = io.BytesIO(base64.b64decode(qr_code.qr_code))
            qr_stream.seek(0)
        return qr_stream


query_executor = CacheableQueryExecutor(event_prefixes=["qrcode", "photo"])
repository_qrcode = QRCodeRepository(query_executor=query_executor)
