import html
import re
import logging
from typing import Dict, List, Tuple
from core.router import router
from agents.sre import SREAgent
from agents.devsecops import DevSecOpsAgent
from agents.research import ResearchAgent
from agents.specialist import SpecialistAgent
from agents.general import GeneralAgent
from agents.base import BaseAgent

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    def __init__(self):
        self.router = router
        self.agents: Dict[str, BaseAgent] = {
            "sre": SREAgent(),
            "devsecops": DevSecOpsAgent(),
            "research": ResearchAgent(),
            "specialist": SpecialistAgent(),
            "general": GeneralAgent(),
        }
        # In-memory history: {chat_id: [{"role": "user"|"assistant", "content": "..."}]}
        self.histories: Dict[int, List[Dict[str, str]]] = {}

    def get_agent(self, agent_name: str) -> BaseAgent:
        return self.agents.get(agent_name, self.agents["general"])

    def get_history(self, chat_id: int) -> List[Dict[str, str]]:
        if chat_id not in self.histories:
            self.histories[chat_id] = []
        return self.histories[chat_id]

    def add_history(self, chat_id: int, role: str, content: str):
        history = self.get_history(chat_id)
        history.append({"role": role, "content": content})
        # Keep last 10 messages
        if len(history) > 10:
            self.histories[chat_id] = history[-10:]

    async def route_and_execute(
        self,
        chat_id: int,
        user_message: str,
        forced_agent: str = None
    ) -> Tuple[BaseAgent, str, Dict]:
        history = self.get_history(chat_id)

        if forced_agent and forced_agent in self.agents:
            selected_agent = self.get_agent(forced_agent)
            route_info = {
                "agent": forced_agent,
                "confidence": 1.0,
                "reason": f"Chỉ định thủ công qua lệnh /{forced_agent}",
                "task": user_message
            }
        else:
            route_info = await self.router.route(user_message)
            selected_agent = self.get_agent(route_info.get("agent", "general"))

        task = route_info.get("task", user_message)
        response_text = await selected_agent.execute(task=task, chat_history=history)

        # Update chat history
        self.add_history(chat_id, "user", user_message)
        self.add_history(chat_id, "assistant", response_text)

        return selected_agent, response_text, route_info

    @staticmethod
    def chunk_message(text: str, max_length: int = 4000) -> List[str]:
        """Tách tin nhắn dài thành nhiều phần an toàn cho Telegram (max 4096)."""
        if len(text) <= max_length:
            return [text]

        chunks = []
        lines = text.split("\n")
        current_chunk = []
        current_len = 0

        for line in lines:
            line_len = len(line) + 1
            if current_len + line_len > max_length:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_len = line_len
                else:
                    # Line itself is longer than max_length
                    for i in range(0, len(line), max_length):
                        chunks.append(line[i:i + max_length])
                    current_chunk = []
                    current_len = 0
            else:
                current_chunk.append(line)
                current_len += line_len

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

orchestrator = MultiAgentOrchestrator()
