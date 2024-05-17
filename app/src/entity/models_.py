# import enum
# from datetime import date
# from sqlalchemy.orm import relationship, Mapped, mapped_column
# from sqlalchemy.sql.schema import ForeignKey
# from sqlalchemy.sql.sqltypes import DateTime
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import Column, Integer, String, Date, Boolean, func, Enum
# from sqlalchemy.dialects.postgresql import ENUM


# Base = declarative_base()

# class Role(enum.Enum):
#     admin: str = "admin"
#     moderator: str = "moderator"
#     user: str = "user"

# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True)
#     username = Column(String(50))
#     email = Column(String(250), nullable=False, unique=True)
#     password = Column(String(255), nullable=False)
#     created_at = Column("created_at", DateTime, default=func.now())
#     avatar = Column(String(255), nullable=True)
#     refresh_token = Column(String(255), nullable=True)
#     created_at = Column(DateTime, default=func.now())
#     updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
#     role = Column(ENUM('admin', 'moderator', 'user', name='role'), default='user', nullable=True)
#     isLoggedIn = Column(Boolean, default=False)
#     confirmed = Column(Boolean, default=False)