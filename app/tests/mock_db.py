import sys
import os
# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from src.entity.models import Comment, User, Photo, Base

class MockDB():
    def __init__(self, users: list|None = None, photos: list|None = None, comments: list|None = None):
        self.SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
        self.users = users
        self.photos = photos
        self.comments = comments
    
    def __call__(self) -> Session:
        self.setup_engine()
        self.conn = self.create_connection()
        if self.users is not None:
            self.fill_users()
        if self.photos is not None:
            self.fill_photos()
        if self.comments is not None:
            self.fill_comments()

        return self.conn

    def setup_engine(self):
        self.engine = create_engine(
            self.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
        self.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)

    def create_connection(self):
        # conn = sqlite3.connect(':memory:')
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

        conn = self.TestingSessionLocal()
        return conn
        # yield conn
        # conn.rollback()
        # conn.close()

    def fill_users(self):
        for user in self.users:
            new_record = User(**user)
            self.conn.add(new_record)
        self.conn.commit()

    def fill_photos(self):
        for photo in self.photos:
            new_record = Photo(**photo)
            self.conn.add(new_record)
        self.conn.commit()

    def fill_comments(self):
        for comment in self.comments:
            new_record = Comment(**comment)
            self.conn.add(new_record)
        self.conn.commit()
