import sys
import os
# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from src.entity.models import Comment, User, Photo, Role, Base

USERS = [
    {
        'email': "admin@myapp.com",
        'password': 'string',
        'confirmed': True,
        'role': Role.admin
    },
    {
        'email': "moderator@myapp.com",
        'password': 'string',
        'confirmed': True,
        'role': Role.moderator
    },
    {
        'email': "first_user@myapp.com",
        'password': 'string',
        'confirmed': True,
        'role': Role.user
    },
    {
        'email': "second_user@myapp.com",
        'password': 'string',
        'confirmed': True,
        'role': Role.user
    }
]

PHOTOS = [
    {'url': 'http://cloud.com/img_1.jpg'},
    {'url': 'http://cloud.com/img_2.jpg'},
    {'url': 'http://cloud.com/img_3.jpg'},
    {'url': 'http://cloud.com/img_4.jpg'},

]

class MockDB():
    def __init__(self, users: list|None = None, photos: list|None = None, comments: list|None = None):
        self.SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
        # self.SQLALCHEMY_DATABASE_URL = "sqlite:///test_bd"
        self.users = users
        self.photos = photos
        self.comments = comments
        self.init_db()
    

    def __call__(self) -> Session:
        conn = self.TestingSessionLocal()

        return conn

    def setup_engine(self):
        self.engine = create_engine(
            self.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False},
        poolclass=StaticPool)
        self.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, expire_on_commit=False, bind=self.engine)

    def init_db(self):
        self.setup_engine()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

        conn = self.TestingSessionLocal()
        if self.users is not None:
            self.fill_users(conn)
        if self.photos is not None:
            self.fill_photos(conn)
        if self.comments is not None:
            self.fill_comments(conn)
        conn.close()

    def fill_users(self, conn):
        for user in self.users:
            new_record = User(**user)
            conn.add(new_record)
        conn.commit()

    def fill_photos(self, conn):
        for photo in self.photos:
            new_record = Photo(**photo)
            conn.add(new_record)
        conn.commit()

    def fill_comments(self, conn):
        for comment in self.comments:
            new_record = Comment(**comment)
            conn.add(new_record)
        conn.commit()
