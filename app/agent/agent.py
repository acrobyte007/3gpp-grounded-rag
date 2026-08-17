import time
import json
from typing import List, Tuple, Optional, Dict
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import traceable
from langchain_core.messages import ToolMessage
from app.agent.llm_client import get_llm
from app.agent.tools import tools
from app.agent.schemas import UserContext, RAGResponse
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.guardrails import get_pii_middleware, get_retry_middleware
from logger.logger import get_logger

logger = get_logger(__name__)


class RAGAgentManager:
    def __init__(self):
        self.llm = None
        self.agent = None
        self._initialized = False

    def initialize(self):
        """Initialize the RAG agent."""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing RAG agent...")
            self.llm = get_llm()
            self.agent = create_agent(
                self.llm,
                tools,
                checkpointer=InMemorySaver(),
                context_schema=UserContext,
                system_prompt=SYSTEM_PROMPT,
                middleware=[
                    *get_pii_middleware(),
                    *get_retry_middleware(),
                ],
                response_format=RAGResponse
            )
            self._initialized = True
            logger.info("RAG agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG agent: {str(e)}")
            raise

    @traceable(run_type="llm")
    async def get_answer(
        self,
        namespace: str,
        query: str,
        doc_ids: List[str],
        conversation_id: Optional[str] = None,
    ) -> Tuple[str, Optional[List[Dict]]]:
        if not self._initialized:
            self.initialize()
        
        logger.info(f"Getting RAG answer for query: {query}")
        
        thread_config = {"configurable": {"thread_id": conversation_id}}
        
        start_time = time.time()
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": query}]},
            thread_config,
            context=UserContext(namespace=namespace, doc_ids=doc_ids)
        )
        response = result["structured_response"]
        end_time = time.time()
        logger.info(f"RAG answer generated in {end_time - start_time:.2f} seconds")
        
        return response.answer

rag_agent = RAGAgentManager()
