import json
import logging
from typing import AsyncGenerator, Dict, List, Optional
import httpx

from config import OPENAI_BASE_URL, OPENAI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, base_url: str = OPENAI_BASE_URL, api_key: str = OPENAI_API_KEY, model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: float = 60.0
    ) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        req_timeout = httpx.Timeout(connect=15.0, read=timeout, write=15.0, pool=15.0)

        async with httpx.AsyncClient(timeout=req_timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"LLM request failed [{response.status_code}]: {error_text.decode('utf-8', errors='ignore')}")
                    raise RuntimeError(f"LLM returned status {response.status_code}")

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: float = 60.0
    ) -> str:
        collected = []
        async for chunk in self.stream_chat(messages, model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout):
            collected.append(chunk)
        return "".join(collected)

llm_client = LLMClient()
