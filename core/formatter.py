import re
import html
from typing import List

def format_telegram_html(text: str) -> str:
    """
    Converts standard Markdown into valid, clean Telegram HTML.
    Prevents entity parse errors and escapes dangerous tags like <unknown>.
    """
    if not text:
        return ""

    # 1. Replace <br> variants with newline
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # 2. Protect and extract code blocks: ```lang ... ```
    code_blocks = []
    def save_code_block(match):
        lang = (match.group(1) or "").strip()
        code = match.group(2)
        code_blocks.append((lang, code))
        return f"___CODE_BLOCK_{len(code_blocks)-1}___"

    text = re.sub(r"```([a-zA-Z0-9_-]*)\n?(.*?)```", save_code_block, text, flags=re.DOTALL)

    # 3. Protect and extract inline code: `code`
    inline_codes = []
    def save_inline_code(match):
        inline_codes.append(match.group(1))
        return f"___INLINE_CODE_{len(inline_codes)-1}___"

    text = re.sub(r"`([^`\n]+)`", save_inline_code, text)

    # 4. Handle LaTeX math: $$...$$ and $...$
    def save_math_block(match):
        math_content = match.group(1).strip()
        inline_codes.append(math_content)
        return f"___INLINE_CODE_{len(inline_codes)-1}___"

    text = re.sub(r"\$\$(.*?)\$\$", save_math_block, text, flags=re.DOTALL)
    text = re.sub(r"\$([^\$\n]+)\$", save_math_block, text)

    # 5. Extract blockquotes before escaping
    blockquotes = []
    def save_blockquote(match):
        bq_content = match.group(1).strip()
        blockquotes.append(bq_content)
        return f"___BLOCKQUOTE_{len(blockquotes)-1}___"

    text = re.sub(r"^>\s*(.+)$", save_blockquote, text, flags=re.MULTILINE)

    # 6. Escape all raw text (turns <unknown> into &lt;unknown&gt;, & into &amp;)
    text = html.escape(text, quote=False)

    # 7. Convert Markdown Headers: # Title -> <b>Title</b>
    text = re.sub(r"^#{1,6}\s*(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # 8. Convert Bold: **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # 9. Convert Italic: *text* or _text_
    text = re.sub(r"(?<!\w)\*([^*\n]+?)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_([^_\n]+?)_(?!\w)", r"<i>\1</i>", text)

    # 10. Restore blockquotes (format internal markdown safely)
    for i, bq in enumerate(blockquotes):
        esc_bq = html.escape(bq, quote=False)
        esc_bq = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc_bq)
        text = text.replace(f"___BLOCKQUOTE_{i}___", f"<blockquote>{esc_bq}</blockquote>")

    # 11. Restore inline codes (properly escaped)
    for i, code in enumerate(inline_codes):
        esc = html.escape(code, quote=False)
        text = text.replace(f"___INLINE_CODE_{i}___", f"<code>{esc}</code>")

    # 12. Restore code blocks (properly escaped)
    for i, (lang, code) in enumerate(code_blocks):
        esc = html.escape(code.strip("\n"), quote=False)
        if lang:
            tag = f'<pre><code class="language-{lang}">{esc}</code></pre>'
        else:
            tag = f"<pre><code>{esc}</code></pre>"
        text = text.replace(f"___CODE_BLOCK_{i}___", tag)

    return text

def strip_html_tags(text: str) -> str:
    """Fallback: strips HTML tags to ensure clean plain text."""
    clean = re.sub(r"<[^>]+>", "", text)
    return html.unescape(clean)

def chunk_markdown(text: str, max_chars: int = 2800) -> List[str]:
    """
    Splits long Markdown text into chunks of <= max_chars,
    preserving code blocks and paragraph boundaries.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = []
    current_len = 0
    in_code_block = False
    code_lang = ""

    for para in paragraphs:
        if len(para) > max_chars:
            lines = para.split("\n")
            for line in lines:
                line_len = len(line) + 1
                if current_len + line_len > max_chars and current_chunk:
                    chunk_str = "\n".join(current_chunk)
                    if in_code_block:
                        chunk_str += "\n```"
                    chunks.append(chunk_str)

                    current_chunk = []
                    current_len = 0
                    if in_code_block:
                        current_chunk.append(f"```{code_lang}")
                        current_len = len(code_lang) + 4

                current_chunk.append(line)
                current_len += line_len
                for marker in re.finditer(r"```([a-zA-Z0-9_-]*)", line):
                    if not in_code_block:
                        in_code_block = True
                        code_lang = marker.group(1)
                    else:
                        in_code_block = False
                        code_lang = ""
            continue

        para_len = len(para) + 2
        if current_len + para_len > max_chars and current_chunk:
            chunk_str = "\n\n".join(current_chunk)
            if in_code_block:
                chunk_str += "\n```"
            chunks.append(chunk_str)

            current_chunk = []
            current_len = 0
            if in_code_block:
                current_chunk.append(f"```{code_lang}")
                current_len = len(code_lang) + 4

        current_chunk.append(para)
        current_len += para_len

        for marker in re.finditer(r"```([a-zA-Z0-9_-]*)", para):
            if not in_code_block:
                in_code_block = True
                code_lang = marker.group(1)
            else:
                in_code_block = False
                code_lang = ""

    if current_chunk:
        chunk_str = "\n\n".join(current_chunk)
        if in_code_block:
            chunk_str += "\n```"
        chunks.append(chunk_str)

    return chunks

def render_messages(header_html: str, markdown_body: str, max_chars: int = 2800) -> List[str]:
    """
    Renders header + markdown body into a list of valid Telegram HTML messages.
    First message includes header_html.
    """
    chunks = chunk_markdown(markdown_body, max_chars=max_chars)
    formatted_chunks = []

    for i, ch in enumerate(chunks):
        formatted_html = format_telegram_html(ch)
        if i == 0:
            formatted_chunks.append(header_html + formatted_html)
        else:
            formatted_chunks.append(formatted_html)

    return formatted_chunks
