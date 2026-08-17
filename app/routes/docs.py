from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List
from app.services.auth import get_current_user
from app.database.database import db_manager
from app.database.repositories import DocumentRepository
from app.database.pincone_db import pinecone_service
from app.services.filebase import storage
from logger.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/")
async def get_all_documents(
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )

        async with db_manager.connect() as session:
            doc_repo = DocumentRepository(session)
            documents = await doc_repo.get_documents_by_user(user_id)
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "documents": [
                        {
                            "id": str(doc.id),
                            "file_name": doc.file_name,
                            "file_type": doc.file_type,
                            "file_size": doc.file_size,
                            "chunks": doc.chunks,
                            "primary_language": doc.primary_language,
                            "created_at": doc.created_at.isoformat() if doc.created_at else None,
                            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
                        }
                        for doc in documents
                    ]
                }
            )

    except Exception as e:
        logger.error(f"Failed to get documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(e)}"
        )


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )

        async with db_manager.connect() as session:
            doc_repo = DocumentRepository(session)
            document = await doc_repo.get_document_by_id(document_id)
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            if str(document.user_id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this document"
                )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": str(document.id),
                    "file_name": document.file_name,
                    "file_type": document.file_type,
                    "file_size": document.file_size,
                    "filebase_key": document.filebase_key,
                    "filebase_url": document.filebase_url,
                    "bucket_name": document.bucket_name,
                    "chunks": document.chunks,
                    "primary_language": document.primary_language,
                    "created_at": document.created_at.isoformat() if document.created_at else None,
                    "updated_at": document.updated_at.isoformat() if document.updated_at else None
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )

        async with db_manager.connect() as session:
            doc_repo = DocumentRepository(session)
            document = await doc_repo.get_document_by_id(document_id)
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            if str(document.user_id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this document"
                )

            if document.filebase_key:
                try:
                    storage.delete_document(document.filebase_key)
                    logger.info(f"Deleted document {document.filebase_key} from storage")
                except Exception as e:
                    logger.error(f"Failed to delete from storage: {str(e)}")

            try:
                pinecone_service.delete(
                    namespace=str(user_id),
                    document_id=document_id
                )
                logger.info(f"Deleted document {document_id} from Pinecone")
            except Exception as e:
                logger.error(f"Failed to delete from Pinecone: {str(e)}")

            await doc_repo.delete_document(document_id)

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "Document deleted successfully",
                    "document_id": document_id
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )