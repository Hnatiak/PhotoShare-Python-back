from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Boolean, func
import enum
from sqlalchemy.dialects.postgresql import ENUM

Base = declarative_base()

class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column("created_at", DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    role = Column(ENUM('admin', 'moderator', 'user', name='role'), default='user', nullable=True)
    isLoggedIn = Column(Boolean, default=False)
    confirmed = Column(Boolean, default=False)
    

class BlacklistToken(Base):
    __tablename__ = "blacklist_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), nullable=False, unique=True)
    
class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    photo_id: Mapped[int] = mapped_column(Integer, ForeignKey("photos.id"), nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    user: Mapped["User"] = relationship("User", backref="comments", lazy="joined")
    # photo: Mapped["Photo"] = relationship("Photo", backref="comments", lazy="joined")

class Photo(Base):
    __tablename__ = "photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    user: Mapped["User"] = relationship("User", backref="photos", lazy="joined")
    comments: Mapped[list["Comment"]] = relationship("Comment", backref="photos", lazy="joined")