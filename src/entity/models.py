import enum
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime, func, Enum
from sqlalchemy.orm import DeclarativeBase



class Base(DeclarativeBase):
    pass

class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), index=True)
    last_name = Column(String(50), index=True)
    email = Column(String(50), index=True)
    phone_number = Column(String(50), index=True)
    birthday = Column(Date, index=True)
    additional_data = Column(Boolean, default=False)
    created_at: Mapped[date] = mapped_column('created_at', DateTime, default=func.now(), nullable=True)
    updated_at: Mapped[date] = mapped_column('updated_at', DateTime, default=func.now(), onupdate=func.now(),                                 nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    user: Mapped["User"] = relationship("User", backref="contacts", lazy="joined")

class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[date] = mapped_column('created_at', DateTime, default=func.now())
    updated_at: Mapped[date] = mapped_column('updated_at', DateTime, default=func.now(), onupdate=func.now())
    role: Mapped[Enum] = mapped_column('role', Enum(Role), default=Role.user, nullable=True)

    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)