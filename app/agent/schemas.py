# app/agent/schemas.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


@dataclass
class UserContext:
    """User context for RAG agent."""
    namespace: str
    doc_ids: List[str]


class RAGResponse(BaseModel):
    """Structured response from RAG agent."""
    answer: str = Field(description="The answer to the question")


class Source(BaseModel):
    """Source document chunk."""
    text: str
    document_id: str
    chunk_number: int
    score: float
    language: str = "en"


class RAGResult(BaseModel):
    """Complete RAG result with answer and sources."""
    answer: str
    sources: Optional[List[Source]] = None
    processing_time: Optional[float] = None


class SearchQuery(BaseModel):
    """Search query for vector search."""
    query: str
    namespace: str
    doc_ids: List[str]
    top_k: int = 5


class SearchResult(BaseModel):
    """Search result from vector search."""
    text: str
    document_id: str
    chunk_number: int
    score: float
    language: str = "en"