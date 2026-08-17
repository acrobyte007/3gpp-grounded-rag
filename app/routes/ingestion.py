# app/routes/ingestion.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status
from fastapi.responses import JSONResponse
import os
import tempfile
from app.services.filebase import storage
from app.services.extraction import extract_text
from app.services.cleaning_chunking import process_text
from app.services.embeddings import embedding_service
from app.database.pincone_db import pinecone_service
from app.database.database import db_manager
from app.database.repositories import DocumentRepository
from app.services.auth import get_current_user
from logger.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/docs", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a document, extract text, chunk it, and store embeddings in Pinecone.
    """
    temp_file_path = None
    
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )

        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=os.path.splitext(file.filename)[1]
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            temp_file_path = tmp_file.name

        object_name = storage.upload_document(
            file_name=temp_file_path, 
            object_name=file.filename
        )

        extracted_text = await extract_text(temp_file_path)

        chunks = await process_text(extracted_text)

        texts = [chunk["text"] for chunk in chunks]
        embeddings_result = embedding_service.embed(texts)

        vectors = []
        chunks_list = []
        lang_list = []
        tokens_list = []

        for i, chunk in enumerate(chunks):
            embedding_data = embeddings_result.get(i)
            if not embedding_data:
                continue
                
            vectors.append(embedding_data["embedding"])
            chunks_list.append(chunk["text"])
            lang_list.append(chunk["language"])
            tokens_list.append(embedding_data["tokens"])

        # Use user_id as namespace
        result = pinecone_service.upsert(
            namespace=str(user_id),  # User ID as namespace
            document_id=object_name,
            vectors=vectors,
            chunks=chunks_list,
            lang_list=lang_list,
            tokens_list=tokens_list
        )

        async with db_manager.connect() as session:
            doc_repo = DocumentRepository(session)
            
            document = await doc_repo.create_document(
                user_id=user_id,
                file_name=file.filename,
                file_type=os.path.splitext(file.filename)[1],
                file_size=len(content),
                filebase_key=object_name,
                filebase_url=storage.get_file_url(object_name),
                bucket_name="pdf-doc-docx",
                chunks=len(chunks),
                primary_language=lang_list[0] if lang_list else "en"
            )

        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Document uploaded and processed successfully",
                "file_name": file.filename,
                "document_id": str(document.id),
                "namespace": str(user_id),
                "chunks": len(chunks),
                "primary_language": lang_list[0] if lang_list else "en"
            }
        )

    except ValueError as e:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )