import asyncio
import html
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from config import TELEGRAM_BOT_TOKEN
from core.orchestrator import orchestrator
from core.formatter import render_messages, strip_html_tags

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("hungorwo_bot")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

HELP_TEXT = """🎯 <b>HỆ THỐNG MULTI-AGENT ORCHESTRATOR-WORKER</b>

Bot sử dụng mô hình <b>Supervisor - Specialist Workers</b> chạy trên nền tảng Gemini (9router combo <code>allin-v0.0.1</code>).

🤖 <b>Cách thức hoạt động:</b>
Mỗi tin nhắn gửi đến sẽ qua <b>Supervisor/Router</b> để tự động nhận diện intent và chuyển tiếp cho chuyên gia phù hợp nhất.

🛠️ <b>Danh sách Agent Chuyên Trách:</b>
• 🛠️ <b>SRE Expert:</b> Kubernetes, GPU Infra, Linux kernel, Azure ML, Prometheus/Grafana, troubleshooting sự cố.
• 🛡️ <b>DevSecOps Expert:</b> Audit manifest, CVE triage, container security, least privilege, CI/CD hardening.
• 🔍 <b>Research Expert:</b> Nghiên cứu AI, ArXiv papers, phân tích kiến trúc mô hình & xu hướng công nghệ.
• 🔬 <b>Domain Specialist:</b> Y học hàn lâm, lịch sử thế giới, khoa học tự nhiên.
• 🤖 <b>General Assistant:</b> Giao tiếp thông thường & giải đáp đa lĩnh vực.

⚡ <b>Lệnh trực tiếp (Bypass Router):</b>
/sre <i>&lt;yêu cầu&gt;</i> - Gặp trực tiếp SRE Expert
/sec <i>&lt;yêu cầu&gt;</i> - Gặp trực tiếp DevSecOps Expert
/research <i>&lt;yêu cầu&gt;</i> - Gặp trực tiếp Research Expert
/agents - Xem chi tiết năng lực các Agent
/help - Xem hướng dẫn này
"""

@dp.message(CommandStart())
async def handle_start(message: Message):
    await message.answer(HELP_TEXT, parse_mode=ParseMode.HTML)

@dp.message(Command("help"))
async def handle_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode=ParseMode.HTML)

@dp.message(Command("agents"))
async def handle_agents(message: Message):
    text = """📋 <b>CHI TIẾT NĂNG LỰC CÁC AGENT</b>

1. 🛠️ <b>SRE & Infrastructure Expert</b> (<code>sre</code>)
   - Chuyên sâu: Kubernetes (DRA, PodGroup, Kueue, Operators), GPU Clusters (NVLink, NCCL), Linux tuning, PromQL.

2. 🛡️ <b>DevSecOps & Security Architect</b> (<code>devsecops</code>)
   - Chuyên sâu: Pod Security Standards, RBAC, NetworkPolicy, CVE analysis, Dockerfile/K8s YAML hardening, CIS benchmarks.

3. 🔍 <b>Deep Tech & AI Research Analyst</b> (<code>research</code>)
   - Chuyên sâu: Mô hình Reasoning, Transformers, MoE, Paper reviews, benchmark & so sánh kỹ thuật.

4. 🔬 <b>Domain & Academic Scholar</b> (<code>specialist</code>)
   - Chuyên sâu: Y học (Evidence-based), Lịch sử thế giới, Khoa học hàn lâm.

5. 🤖 <b>General Assistant</b> (<code>general</code>)
   - Xử lý các câu hỏi tổng quát và điều phối thông tin.
"""
    await message.answer(text, parse_mode=ParseMode.HTML)

async def process_user_query(message: Message, query_text: str, forced_agent: str = None):
    chat_id = message.chat.id
    if not query_text.strip():
        await message.reply("Vui lòng nhập nội dung câu hỏi kèm theo lệnh. Ví dụ: <code>/sre Pod bị OOMKilled xử lý sao?</code>", parse_mode=ParseMode.HTML)
        return

    # 1. Progressive Status
    await bot.send_chat_action(chat_id, "typing")
    status_msg = await message.reply("🎯 <i>[Router] Đang phân tích ngữ cảnh và điều phối chuyên gia...</i>", parse_mode=ParseMode.HTML)

    try:
        # 2. Route and Execute
        agent, answer, route_info = await orchestrator.route_and_execute(
            chat_id=chat_id,
            user_message=query_text,
            forced_agent=forced_agent
        )

        escaped_title = html.escape(agent.title)
        escaped_reason = html.escape(route_info.get("reason", ""))
        header = f"{agent.icon} <b>[{escaped_title}]</b>\n<i>💡 Điều phối: {escaped_reason}</i>\n\n"

        # Format and chunk into valid Telegram HTML messages
        messages = render_messages(header, answer, max_chars=3200)

        # Edit first chunk into status_msg
        first_chunk = messages[0]
        try:
            await status_msg.edit_text(first_chunk, parse_mode=ParseMode.HTML)
        except TelegramBadRequest:
            await status_msg.edit_text(strip_html_tags(first_chunk), parse_mode=None)

        # Send subsequent chunks if any
        for chunk in messages[1:]:
            try:
                await message.answer(chunk, parse_mode=ParseMode.HTML)
            except TelegramBadRequest:
                await message.answer(strip_html_tags(chunk), parse_mode=None)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ <b>Lỗi xử lý:</b> <code>{str(e)}</code>", parse_mode=ParseMode.HTML)

@dp.message(Command("sre"))
async def cmd_sre(message: Message):
    query = message.text.replace("/sre", "", 1).strip()
    await process_user_query(message, query, forced_agent="sre")

@dp.message(Command("sec"))
async def cmd_sec(message: Message):
    query = message.text.replace("/sec", "", 1).strip()
    await process_user_query(message, query, forced_agent="devsecops")

@dp.message(Command("research"))
async def cmd_research(message: Message):
    query = message.text.replace("/research", "", 1).strip()
    await process_user_query(message, query, forced_agent="research")

@dp.message()
async def handle_message(message: Message):
    if not message.text:
        return
    await process_user_query(message, message.text, forced_agent=None)

async def main():
    logger.info("Starting hungorwo_bot Multi-Agent Orchestrator...")
    # Delete webhook to ensure polling works cleanly
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
