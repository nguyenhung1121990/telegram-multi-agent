import json
import logging
from typing import Dict, Any
from core.llm import llm_client

logger = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = """Bạn là Supervisor / Router của hệ thống Multi-Agent AI trên Telegram.
Nhiệm vụ của bạn là phân tích tin nhắn của người dùng và quyết định chuyển giao cho Agent Chuyên Gia phù hợp nhất.

Hệ thống có các Agent chuyên trách sau:
1. `sre`: Chuyên gia SRE, Kubernetes, Cloud (Azure/AWS), hạ tầng GPU, Linux OS, networking, tuning hiệu năng, giám sát Prometheus/Grafana, chẩn đoán sự cố hệ thống.
2. `devsecops`: Chuyên gia Bảo mật thông tin, DevSecOps, đánh giá lỗ hổng (CVE), bảo mật container/K8s (RBAC, Pod Security), SAST/DAST, audit mã nguồn/manifest, tuân thủ an toàn bảo mật.
3. `research`: Chuyên gia Nghiên cứu & Tin tức, tổng hợp thông tin chuyên sâu, công nghệ AI mới, papers, phân tích xu hướng công nghệ cao cấp.
4. `specialist`: Chuyên gia các lĩnh vực học thuật chuyên biệt như Y học, Dược học, Lịch sử, Địa lý học, Pháp lý.
5. `general`: Trợ lý tổng quát dùng cho chào hỏi, giao tiếp thông thường hoặc các câu hỏi kiến thức phổ thông không thuộc 4 lĩnh vực trên.

Quy tắc bắt buộc:
- BẠN CHỈ TRẢ VỀ DUY NHẤT 1 ĐOẠN MÃ JSON HỢP LỆ (không kèm markdown ```json ``` hay lời giải thích nào khác).
- Định dạng JSON:
{
  "agent": "sre" | "devsecops" | "research" | "specialist" | "general",
  "confidence": 0.0 đến 1.0,
  "reason": "Giải thích ngắn gọn lý do chọn (1 câu tiếng Việt)",
  "task": "Nội dung yêu cầu được tinh chỉnh rõ ràng cho agent"
}
"""

class OrchestratorRouter:
    def __init__(self):
        self.client = llm_client

    async def route(self, user_message: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Yêu cầu của người dùng:\n{user_message}"}
        ]

        try:
            raw_response = await self.client.generate_text(messages, temperature=0.1, max_tokens=500)
            cleaned = raw_response.strip()
            # Clean possible markdown wrapping
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()

            result = json.loads(cleaned)
            agent = result.get("agent", "general")
            if agent not in ["sre", "devsecops", "research", "specialist", "general"]:
                agent = "general"
            result["agent"] = agent
            return result
        except Exception as e:
            logger.warning(f"Router parse failed: {e}. Falling back to general agent.")
            return {
                "agent": "general",
                "confidence": 0.5,
                "reason": "Phân tích tự động gặp lỗi, chuyển về trợ lý chung.",
                "task": user_message
            }

router = OrchestratorRouter()
