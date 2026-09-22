from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from core.llm import llm_client

class BaseAgent(ABC):
    def __init__(self, name: str, icon: str, title: str, system_prompt: str):
        self.name = name
        self.icon = icon
        self.title = title
        self.system_prompt = system_prompt
        self.client = llm_client

    async def execute(self, task: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        if chat_history:
            # Append recent history (up to last 6 messages)
            messages.extend(chat_history[-6:])
        messages.append({"role": "user", "content": task})

        response = await self.client.generate_text(
            messages=messages,
            temperature=0.2,
            max_tokens=4096
        )
        return response.strip()
