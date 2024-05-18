import io
import uuid
import enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import UUID, Column, Integer, LargeBinary, String, Date, Boolean, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import Enum

Base = declarative_base()

class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"

class AssetType(enum.Enum):
    origin: str = 'origin'
    avatar: str = 'avatar'
    greyscale: str = 'greyscale'
    delete_bg: str = 'delete_bg'
    oil_paint: str = 'oil_paint'
    sepia: str = 'sepia'
    outline: str = 'outline'

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
    role = Column(ENUM(Role), default=Role.user, nullable=True)
    isLoggedIn = Column(Boolean, default=False)
    confirmed = Column(Boolean, default=False)


class BlacklistToken(Base):
    __tablename__ = 'blacklist_tokens'
    id = Column(Integer, primary_key=True)
    token = Column(String(500), unique=True, nullable=False)
    blacklisted_on = Column(DateTime, default=func.now())
    
class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    photo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("photos.id"), nullable=False)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    user: Mapped["User"] = relationship("User", backref="comments", lazy="joined")
    photo: Mapped["Photo"] = relationship("Photo", backref="comments", lazy="joined")

# table for photo and tag relationship
class PhotoTag(Base):
    __tablename__ = "phototags"
    id: Mapped[int] = mapped_column(primary_key=True)
    photo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("photos.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)


class Photo(Base):
    __tablename__ = "photos"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    # original_id: Mapped[uuid.UUID] = mapped_column(UUID, default=None)
    asset_type = Column(ENUM(AssetType), default='origin', nullable=True)
    created_at = Column("created_at", DateTime, default=func.now(), index=True)
    updated_at = Column("updated_at", DateTime, default=func.now())
    user_id = Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), default=None)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)    
    description: Mapped[str] = mapped_column(String(2200), nullable=True, index=True)
    tags: Mapped[list["Tag"]] = relationship(secondary='phototags', back_populates='photos', lazy="joined")
    user = relationship("User", backref="photos")


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at = Column("created_at", DateTime, default=func.now())
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    photos: Mapped[list["Photo"]] = relationship(secondary='phototags', back_populates='tags', lazy="joined")

class QRCode(Base):
    __tablename__ = "qr_codes"
    id: Mapped[int] = mapped_column(primary_key=True)
    photo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("photos.id"), nullable=False)
    qr_code: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)