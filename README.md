# 🤖 Telegram Multi-Agent Orchestrator

A production-ready Telegram Bot implementing the **Supervisor – Specialist Workers (Orchestrator-Worker)** architecture. 

It uses an LLM-based Router to analyze user intent in real time, delegate tasks to domain-specific Specialist Agents, and render rich responses safely via a custom Telegram HTML formatting engine.

---

## 📐 Architecture & Workflow

```text
                  [ User on Telegram ]
                           │ (Message / Slash Command)
                           ▼
                 [ aiogram 3.x Gateway ]
                           │
                 [ Supervisor / Router ]
                           │ (Intent Classification -> JSON Plan)
          ┌────────────────┼────────────────┬────────────────┐
          ▼                ▼                ▼                ▼
     🛠️ SRE Expert   🛡️ DevSecOps     🔍 Research     🔬 Domain / General
     (K8s, GPU,      (Security, CVE,  (AI Papers,     (Medicine, History,
      Linux, SRE)     RBAC, Auditing)  Tech Trends)    Chit-chat)
          └────────────────┼────────────────┴────────────────┘
                           ▼
             [ Telegram HTML Formatter ]
              - Escape technical tags (<unknown>, <pod>)
              - Format Code Blocks, Inline Code, Blockquotes
              - Convert Math ($$...$$) to code blocks
              - Smart Chunking (<= 3500 chars without breaking code)
                           ▼
                  [ Delivered to User ]
```

---

## 📂 Project Structure

```text
telegram-multi-agent/
├── .env                     # Environment variables (Bot token, LLM credentials)
├── pyproject.toml           # Project dependencies
├── config.py                # Configuration loader
├── main.py                  # aiogram 3.x bot entrypoint, handlers & commands
├── core/
│   ├── llm.py               # Async streaming LLM client (OpenAI-compatible)
│   ├── router.py            # Supervisor prompt & intent classification
│   ├── orchestrator.py      # Multi-agent coordinator & session history
│   └── formatter.py         # Markdown -> Telegram HTML & safe chunking engine
└── agents/
    ├── base.py              # Abstract BaseAgent class
    ├── sre.py               # SRE & Cloud Platform Expert
    ├── devsecops.py         # DevSecOps & Security Architect
    ├── research.py          # Deep Tech & AI Research Analyst
    ├── specialist.py        # Domain Scholar (Medicine, History, Science)
    └── general.py           # General & Conversational Assistant
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or `pip`
- A Telegram Bot token (from [@BotFather](https://t.me/BotFather))
- An OpenAI-compatible LLM endpoint (e.g. OpenAI, 9router, LiteLLM, Ollama, vLLM)

### 2. Installation
```bash
# Clone or enter the project directory
cd telegram-multi-agent

# Create virtual environment with uv
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install "aiogram>=3.17.0" "httpx>=0.28.0" "pydantic>=2.10.0" "python-dotenv>=1.0.0"
```

### 3. Configuration (`.env`)
Create a `.env` file in the project root:
```env
TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here"
OPENAI_BASE_URL="http://127.0.0.1:20128/v1"
OPENAI_API_KEY="your_api_key_here"
DEFAULT_MODEL="allin-v0.0.1"
```

### 4. Running Locally
```bash
python main.py
```

---

## 🛠️ How to Extend for Future Use-Cases

### 1. Adding a New Specialist Worker (e.g., `FinOpsAgent`)

#### Step A: Create `agents/finops.py`
```python
from agents.base import BaseAgent

FINOPS_SYSTEM_PROMPT = """Bạn là Senior FinOps & Cloud Cost Optimization Expert.
Thế mạnh:
- Phân tích chi phí Cloud (AWS/Azure/GCP) và Kubernetes cost allocation (Kubecost).
- Tối ưu hóa GPU/CPU reservation, Spot instances, Karpenter consolidation.
- Đưa ra chiến lược cắt giảm chi phí hạ tầng có số liệu chứng minh.
"""

class FinOpsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="finops",
            icon="💰",
            title="Cloud FinOps & Cost Architect",
            system_prompt=FINOPS_SYSTEM_PROMPT
        )
```

#### Step B: Register the Agent in `core/router.py`
Update `ROUTER_SYSTEM_PROMPT` to add the new agent:
```python
# In ROUTER_SYSTEM_PROMPT:
# 6. `finops`: Chuyên gia tối ưu hóa chi phí hạ tầng, cloud billing, Kubecost.
```
And add `"finops"` to the allowed agent list:
```python
if agent not in ["sre", "devsecops", "research", "specialist", "general", "finops"]:
    agent = "general"
```

#### Step C: Register in `core/orchestrator.py`
```python
from agents.finops import FinOpsAgent

# In __init__:
self.agents["finops"] = FinOpsAgent()
```

#### Step D: Add Slash Command in `main.py`
```python
@dp.message(Command("finops"))
async def cmd_finops(message: Message):
    query = message.text.replace("/finops", "", 1).strip()
    await process_user_query(message, query, forced_agent="finops")
```

---

### 2. Switching LLM Providers or Models

Any OpenAI-compatible provider can be plugged in by modifying `.env`:

* **Official OpenAI:**
  ```env
  OPENAI_BASE_URL=https://api.openai.com/v1
  OPENAI_API_KEY=sk-...
  DEFAULT_MODEL=gpt-4o
  ```
* **Local Ollama / vLLM:**
  ```env
  OPENAI_BASE_URL=http://localhost:11434/v1
  OPENAI_API_KEY=ollama
  DEFAULT_MODEL=qwen2.5-coder:32b
  ```
* **DeepSeek / OpenRouter:**
  ```env
  OPENAI_BASE_URL=https://openrouter.ai/api/v1
  OPENAI_API_KEY=sk-or-...
  DEFAULT_MODEL=deepseek/deepseek-r1
  ```

---

### 3. Production Deployment with `systemd`

To run the bot as a persistent background daemon that restarts on crash or reboot:

1. Create user systemd service file:
   `~/.config/systemd/user/hungorwo-bot.service`

```ini
[Unit]
Description=Hungorwo Multi-Agent Orchestrator Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/azureuser/telegram-multi-agent/.venv/bin/python /home/azureuser/telegram-multi-agent/main.py
WorkingDirectory=/home/azureuser/telegram-multi-agent
Environment="PATH=/home/azureuser/telegram-multi-agent/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Restart=always
RestartSec=5
KillMode=mixed
KillSignal=SIGTERM
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

2. Reload, enable, and start:
```bash
systemctl --user daemon-reload
systemctl --user enable --now hungorwo-bot.service
```

3. Manage and view logs:
```bash
# Check status
systemctl --user status hungorwo-bot.service

# Live logs
journalctl --user -u hungorwo-bot.service -f

# Restart
systemctl --user restart hungorwo-bot.service
```

---

## 🛡️ Key Robustness Features (Why this setup doesn't break)

1. **Anti-Formatting-Crash (`core/formatter.py`):**
   - Raw markdown parsers crash when encountering unescaped underscores (`_`), tech tags (`<unknown>`, `<pod-ip>`), or unclosed blocks.
   - The included custom formatter converts Markdown safely into **Telegram HTML**, pre-escapes text, and safely wraps code blocks.
2. **Smart Chunking:**
   - Messages exceeding Telegram's 4096-character limit are split on paragraph boundaries.
   - Code blocks that span chunks are automatically closed and reopened with matching language tags.
3. **Graceful Fallbacks:**
   - If Telegram rejects any HTML entity, it strips HTML tags on the fly and sends clean plain text instead of failing.
4. **Independent Token Isolation:**
   - Runs on its own Telegram Bot Token without conflicting with other bot processes on the same server.
