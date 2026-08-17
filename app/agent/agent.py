import time
from dataclasses import dataclass
from typing import List
from langchain_mistralai import ChatMistralAI


mistral_primary = ChatMistralAI(
    model="ministral-8b-latest",
    temperature=0.7,
    max_retries=2,
    timeout=60,
)

@dataclass
class UserContext:
    namespace: str
    doc_ids: List[str]


def should_retry(error: Exception) -> bool:
    if isinstance(error, TimeoutError):
        return True
    if hasattr(error, "status_code"):
        return error.status_code in (429, 503)
    return False