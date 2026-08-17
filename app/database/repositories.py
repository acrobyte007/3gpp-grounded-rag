# app/database/repositories/user_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Document, User
from app.services.auth import hash_password, verify_password
from typing import Optional,List
import uuid

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, username: str, email: str, password: str) -> User:
        hashed_password = hash_password(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = await self.get_user_by_username(username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(
        self,
        user_id: str,
        file_name: str,
        file_type: str,
        file_size: int,
        filebase_key: str,
        filebase_url: str,
        bucket_name: str,
        chunks: int,
        primary_language: str
    ) -> Document:
        document = Document(
            user_id=user_id,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            filebase_key=filebase_key,
            filebase_url=filebase_url,
            bucket_name=bucket_name,
            chunks=chunks,
            primary_language=primary_language
        )
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_document_by_id(self, document_id: str) -> Optional[Document]:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_documents_by_user(self, user_id: str) -> List[Document]:
        result = await self.session.execute(
            select(Document).where(Document.user_id == user_id)
        )
        return result.scalars().all()

    async def delete_document(self, document_id: str) -> bool:
        document = await self.get_document_by_id(document_id)
        if not document:
            return False
        await self.session.delete(document)
        await self.session.commit()
        return True