from langchain_mistralai import ChatMistralAI


mistral_primary = ChatMistralAI(
    model="ministral-8b-latest",
    temperature=0.7,
    max_retries=2,
    timeout=60,
)