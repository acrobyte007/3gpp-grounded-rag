from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import os
import tempfile
from typing import List
from services.filebase import storage
from services.extraction import extract_text
from services.cleaning_chunking import process_text
from services.embeddings import embedding_service
from database.pincone_db import pinecone_service

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        object_name = storage.upload_document(file_name=tmp_file_path, object_name=file.filename)

        extracted_text = await extract_text(tmp_file_path)

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

        result = pinecone_service.upsert(
            namespace="documents",
            document_id=object_name,
            vectors=vectors,
            chunks=chunks_list,
            lang_list=lang_list,
            tokens_list=tokens_list
        )

        os.unlink(tmp_file_path)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Document uploaded and processed successfully",
                "file_name": object_name,
                "chunks": len(chunks),
                "upsert_result": result
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")