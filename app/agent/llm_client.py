from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv
import os

load_dotenv()


def get_llm():
    """
    Initialize and return the Mistral LLM client.
    
    Returns:
        ChatMistralAI: Configured Mistral chat model
    """
    return ChatMistralAI(
        model=os.getenv("MISTRAL_MODEL", "ministral-8b-latest"),
        temperature=float(os.getenv("MISTRAL_TEMPERATURE", 0.7)),
        max_retries=int(os.getenv("MISTRAL_MAX_RETRIES", 2)),
        timeout=int(os.getenv("MISTRAL_TIMEOUT", 60)),
    )