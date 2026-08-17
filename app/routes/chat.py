# app/routes/chat.py
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from app.agent.agent import rag_agent
from app.services.auth import get_current_user
from app.database.database import db_manager
from app.database.models import Conversation
from logger.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str = Field(..., description="User's question")
    doc_ids: List[str] = Field(..., description="List of document IDs to search")
    conversation_id: Optional[str] = Field(None, description="Conversation thread ID")


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user"
            )

        if not request.doc_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one document ID is required"
            )

        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
            async with db_manager.connect() as session:
                conversation = Conversation(
                    conversation_uuid=conversation_id,
                    user_id=user_id,
                    meta_data={"doc_ids": request.doc_ids}
                )
                session.add(conversation)
                await session.commit()

        answer = await rag_agent.get_answer(
            namespace=user_id,
            query=request.query,
            doc_ids=request.doc_ids,
            conversation_id=conversation_id
        )

        return ChatResponse(
            answer=answer,
            conversation_id=conversation_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get answer: {str(e)}"
        )