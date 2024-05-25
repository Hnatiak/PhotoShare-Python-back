import io
import base64
import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from sqlalchemy.orm import Session, Query
from src.entity.models import User, QRCode
from src.repository.qrcode import QRCodeRepository
from src.services.cache import CacheableQueryExecutor


class TestAsyncQRCodeRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_session = MagicMock(spec=Session)
        self.mock_session.delete.return_value = None
        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None        
        self.mock_query = MagicMock(spec=Query)
        self.byte_string = b"some bytes here"
        self.bytes = base64.b64encode(self.byte_string)
        self.mock_bytes_io = MagicMock(spec=io.BytesIO)
        self.mock_bytes_io.getvalue.return_value = self.byte_string
        self.user = User(id=1)
        self.photo_id = uuid4()
        self.mock_qrcode = MagicMock(spec=QRCode, id=1, photo_id=self.photo_id, qr_code=self.bytes)
        self.repository = QRCodeRepository(query_executor=AsyncMock(spec=CacheableQueryExecutor))

    async def test_save_qrcode(self):
        qr_code = await self.repository.save_qrcode(self.photo_id, self.mock_bytes_io, self.user, self.mock_session)
        
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.mock_session.refresh.assert_called_once()
        self.assertEqual(qr_code.photo_id, self.photo_id)
        self.assertEqual(qr_code.qr_code, self.bytes)

    async def test_read_qrcode(self):
        self.mock_session.query.return_value = self.mock_query
        self.repository.query_executor.get_first.return_value = self.mock_qrcode
        
        qr_stream = await self.repository.read_qrcode(self.photo_id, self.user, self.mock_session)

        self.mock_session.query.assert_called_once()
        self.assertIsInstance(qr_stream, io.BytesIO)
        self.assertTrue(qr_stream.seekable())
        self.assertEqual(qr_stream.tell(), 0)
        self.assertEqual(qr_stream.getvalue(), self.byte_string)

    async def test_read_qrcode_not_found(self):
        self.mock_session.query.return_value = self.mock_query
        self.repository.query_executor.get_first.return_value = None
        
        qr_stream = await self.repository.read_qrcode(self.photo_id, self.user, self.mock_session)

        self.mock_session.query.assert_called_once()
        self.assertIsNone(qr_stream)
        