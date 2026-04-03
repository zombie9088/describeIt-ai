"""LLM client setup using ChatOpenAI and OpenAIEmbeddings."""

import httpx
import os
from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Create HTTP client with SSL verification disabled for local/dev environments
_client = httpx.Client(verify=False)


@lru_cache(maxsize=1)
def get_llm():
    """Get the configured LLM instance.

    Uses lru_cache to ensure only one instance is created per session.
    """
    return ChatOpenAI(
        base_url=os.getenv("api_endpoint"),
        api_key=os.getenv("api_key"),
        model="azure/genailab-maas-gpt-35-turbo",
        http_client=_client,
        temperature=0.7
    )


@lru_cache(maxsize=1)
def get_embedding_model():
    """Get the configured embedding model instance.

    Used for consistency checking and semantic similarity.
    """
    return OpenAIEmbeddings(
        base_url=os.getenv("api_endpoint"),
        api_key=os.getenv("api_key"),
        model="azure/genailab-maas-text-embedding-3-large",
        http_client=_client
    )


# Export as module-level variables for backward compatibility
llm = get_llm()
embedding_model = get_embedding_model()
