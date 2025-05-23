import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)
    refresh_token = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    encryption_key = Column(String, unique=True, index=True)
    sensitive_data = relationship("UserSensitiveData", back_populates="user", uselist=False)

class UserSensitiveData(Base):
    __tablename__ = "user_sensitive_data"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    encrypted_bio = Column(String)
    encrypted_refresh_token = Column(String, nullable=True)
    user = relationship("User", back_populates="sensitive_data")
