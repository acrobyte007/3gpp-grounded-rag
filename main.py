from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.database import db_manager
from app.services.embeddings import embedding_service
from app.database.pincone_db import pinecone_service
from app.services.filebase import storage
from app.agent.agent import rag_agent
from app.routes.auth import router as auth_router
from app.routes.ingestion import router as ingestion_router
from app.routes.docs import router as docs_router
from app.routes.chat import router as chat_router
from logger.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application initialization...")
    
    await db_manager.initialize()
    await embedding_service.initialize()
    rag_agent.initialize()
    pinecone_service.initialize()
    storage.initialize()

    logger.info("Application initialization complete")
    
    try:
        yield
    finally:
        logger.info("Shutting down application...")

        try:
            await db_manager.close_all()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}", exc_info=True)
        
        try:
            if hasattr(pinecone_service, 'close'):
                pinecone_service.close()
                logger.info("Pinecone service closed")
        except Exception as e:
            logger.error(f"Error closing pinecone: {e}", exc_info=True)
        
        logger.info("Shutdown complete")


app = FastAPI(
    title="RAG API",
    version="1.0",
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(ingestion_router)
app.include_router(docs_router)
app.include_router(chat_router)