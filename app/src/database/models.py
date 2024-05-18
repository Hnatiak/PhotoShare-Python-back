import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import UUID, Column, Integer, String, Date, Boolean, func


Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column("created_at", DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)


# table for photo and tag relationship
class PhotoTag(Base):
    __tablename__ = "phototags"
    id: Mapped[int] = mapped_column(primary_key=True)
    photo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("photos.id"))
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))


class Photo(Base):
    __tablename__ = "photos"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    # original_id: Mapped[uuid.UUID] = mapped_column(UUID, default=None)
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

