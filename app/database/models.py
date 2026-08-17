import uuid
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, JSON, Uuid
from sqlalchemy.orm import Mapped, relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = Column(Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, default=func.now(), onupdate=func.now())

    documents = relationship("Document", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

class Document(Base):
    __tablename__ = 'documents'

    id: Mapped[uuid.UUID] = Column(Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    file_name = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    filebase_key = Column(String, nullable=True, unique=True)
    filebase_url = Column(String, nullable=True)
    bucket_name = Column(String, nullable=False, default="pdf-doc-docx")
    chunks = Column(Integer)
    primary_language = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id'))
    user = relationship("User", back_populates="documents")

class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[uuid.UUID] = Column(Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    conversation_uuid = Column(Uuid(as_uuid=True), unique=True, index=True, nullable=False, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id'))
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[uuid.UUID] = Column(Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    conversation_id = Column(Uuid(as_uuid=True), ForeignKey('conversations.id'), index=True, nullable=False)
    role = Column(String)
    content = Column(String)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())

    conversation = relationship("Conversation", back_populates="messages")