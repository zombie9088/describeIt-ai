"""LLM client for Ollama API.

Uses direct HTTP calls to Ollama's API instead of LangChain.
Configure in .env:
    OLLAMA_HOST=http://localhost:11434
    OLLAMA_MODEL=llama3.1  (or any Ollama model)
"""

import httpx
import json
import os
import asyncio
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class OllamaClient:
    """Simple Ollama API client with async support and connection pooling."""

    def __init__(self, host: str = None, model: str = None, timeout: float = 60.0):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        self.timeout = timeout
        # Connection pool with keep-alive for better performance
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            transport=httpx.HTTPTransport(retries=2)
        )
        self._async_client = None

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text using Ollama's generate endpoint.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        url = f"{self.host}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = self._client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.HTTPError as e:
            raise LLMCallError(f"Ollama API request failed: {e}")
        except json.JSONDecodeError as e:
            raise LLMCallError(f"Failed to parse Ollama response: {e}")

    def chat(self, messages: list) -> str:
        """Generate text using Ollama's chat endpoint.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Generated text response
        """
        url = f"{self.host}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }

        try:
            response = self._client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            raise LLMCallError(f"Ollama API request failed: {e}")
        except json.JSONDecodeError as e:
            raise LLMCallError(f"Failed to parse Ollama response: {e}")

    async def generate_async(self, prompt: str, system_prompt: str = None) -> str:
        """Async version of generate for concurrent processing."""
        url = f"{self.host}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
                transport=httpx.AsyncHTTPTransport(retries=2)
            )

        try:
            response = await self._async_client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.HTTPError as e:
            raise LLMCallError(f"Ollama API request failed: {e}")
        except json.JSONDecodeError as e:
            raise LLMCallError(f"Failed to parse Ollama response: {e}")

    async def chat_async(self, messages: list) -> str:
        """Async version of chat for concurrent processing."""
        url = f"{self.host}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }

        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
                transport=httpx.AsyncHTTPTransport(retries=2)
            )

        try:
            response = await self._async_client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except httpx.HTTPError as e:
            raise LLMCallError(f"Ollama API request failed: {e}")
        except json.JSONDecodeError as e:
            raise LLMCallError(f"Failed to parse Ollama response: {e}")

    async def close_async(self):
        """Close the async client when done."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    def invoke(self, prompt: str) -> "OllamaResponse":
        """LangChain-compatible invoke method.

        Args:
            prompt: The prompt string

        Returns:
            OllamaResponse object with content attribute
        """
        content = self.generate(prompt)
        return OllamaResponse(content)

    def is_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            response = self._client.get(f"{self.host}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list:
        """List available models on Ollama server."""
        try:
            response = self._client.get(f"{self.host}/api/tags", timeout=5.0)
            response.raise_for_status()
            result = response.json()
            return [m.get("name", "") for m in result.get("models", [])]
        except Exception:
            return []


class OllamaResponse:
    """Simple response class compatible with LangChain's interface."""

    def __init__(self, content: str):
        self.content = content

    def __str__(self):
        return self.content


class LLMCallError(Exception):
    """Exception raised when LLM call fails."""
    pass


# Global client instance (lazy initialized)
_ollama_client = None


def get_ollama_client() -> OllamaClient:
    """Get the configured Ollama client instance.

    Uses lazy initialization to ensure only one instance is created.
    """
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


# Legacy compatibility - for code that imports 'llm' directly
llm = get_ollama_client()


def check_connection() -> dict:
    """Check Ollama connection and return status info.

    Returns:
        Dict with connection status and available models
    """
    client = get_ollama_client()
    is_available = client.is_available()
    models = client.list_models() if is_available else []

    return {
        "connected": is_available,
        "host": client.host,
        "model": client.model,
        "available_models": models
    }
