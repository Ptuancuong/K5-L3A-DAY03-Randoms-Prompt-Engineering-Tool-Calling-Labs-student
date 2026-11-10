import json
import os
import re
import importlib
from datetime import datetime
from pathlib import Path
import streamlit as st

import tools
importlib.reload(tools)
import chat
importlib.reload(chat)
from chat import run_model_tool_loop
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
TRANSCRIPTS_DIR = ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
load_lab_env(ROOT)

st.set_page_config(page_title="AI Research Agent Demo", page_icon="🤖", layout="wide")
st.title("🤖 AI Research Agent — Lab Day 03")
st.caption("Agent nghiên cứu thông tin đa nguồn: tra cứu báo chí, mạng xã hội X/Twitter, chính sách nội bộ và tính toán số liệu.")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", (value or "").strip())
    return slug.strip("_") or "run"


def get_config():
    system_prompt_path = ROOT / "artifacts" / "system_prompt.md"
    tools_path = ROOT / "artifacts" / "tools.yaml"
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    declarations = load_tool_declarations(tools_path)
    tools = to_openai_tools(declarations)
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai")
    provider = make_provider(provider_name)
    model_name = os.getenv("OPENAI_MODEL", "gemini-3.6-flash")
    version = "v3"
    art_ver = build_artifact_version(version, system_prompt_path, tools_path)
    return provider, system_prompt, tools, model_name, version, art_ver


try:
    provider, system_prompt, tools, model_name, version, art_ver = get_config()
except Exception as exc:
    st.error(f"Lỗi khởi tạo cấu hình: {exc}")
    st.stop()

# Khởi tạo session transcript
if "session_id" not in st.session_state:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    st.session_state.session_id = f"{safe_slug(version)}_{safe_slug(os.getenv('DEFAULT_PROVIDER', 'openai'))}_{timestamp}"
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{st.session_state.session_id}.transcript.json"
    st.session_state.transcript = {
        "session_id": st.session_state.session_id,
        "version": version,
        "provider": os.getenv("DEFAULT_PROVIDER", "openai"),
        "model": model_name,
        **artifact_version_dict(art_ver),
        "started_at": now_iso(),
        "turns": [],
    }
    st.session_state.turn_index = 0

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar thông tin
with st.sidebar:
    st.header("🛠️ Danh sách Tool khả dụng")
    st.markdown("""
    - **`clarify`**: Hỏi lại người dùng khi thiếu thông tin
    - **`calculator`**: Tính toán an toàn *(Tool mới 1)*
    - **`sentiment_analyzer`**: Phân tích sắc thái cảm xúc *(Tool mới 2)*
    - **`crypto_lookup`**: Tra cứu giá tiền mã hóa *(Tool mới 3)*
    - **`timeline`**: Bài đăng gần đây của tài khoản X (handle)
    - **`social_search`**: Tìm kiếm bài đăng theo từ khóa (Top/Latest)
    - **`lookup`**: Tìm kiếm tin tức web (topic / timeframe)
    - **`fetch`**: Đọc chi tiết bài viết từ URL
    - **`format`**: Định dạng danh sách tin thành digest
    - **`send`**: Gửi tin Telegram *(yêu cầu xác nhận)*
    - **`policy`**: Tra cứu chính sách công ty
    - **`papers`**: Tìm bài báo khoa học trên arXiv
    - **`paper_text`**: Đọc nội dung chi tiết bài báo arXiv
    """)
    st.divider()
    st.caption(f"📁 **Transcript:** `{st.session_state.transcript_path.name}`")
    st.caption(f"🔢 **Số lượt đã ghi:** {len(st.session_state.transcript.get('turns', []))}")
    if st.button("Làm mới phiên chat (Tạo transcript mới)"):
        st.session_state.messages = []
        del st.session_state.session_id
        st.rerun()

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("status") == "waiting_for_user":
            st.info("💡 **Agent đang chờ bạn bổ sung thông tin:** Hãy nhập câu trả lời ở ô chat bên dưới để tiếp tục.")
        if "tools" in msg and msg["tools"]:
            with st.expander("🛠️ Chi tiết Tool Calling & Kết quả"):
                for event in msg["tools"]:
                    st.markdown(f"**Tool:** `{event.get('tool')}`")
                    st.json({"args": event.get("args"), "result": event.get("result")})

# Nhận input từ người dùng
if prompt := st.chat_input("Nhập yêu cầu (ví dụ: 'Tính 250*4', 'Tóm tắt bài này', 'Theo policy công ty...')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent đang xử lý, gọi tool và tổng hợp..."):
            st.session_state.turn_index += 1
            start_time = now_iso()

            history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            conv_messages = [{"role": "system", "content": system_prompt}, *history]

            loop_result = run_model_tool_loop(
                provider=provider,
                messages=conv_messages,
                tools=tools,
                model=model_name,
                max_tool_rounds=3,
            )

            assistant_text = loop_result.get("assistant_text", "")
            tool_events = loop_result.get("tool_events", [])
            status = loop_result.get("status", "answered")

            if tool_events:
                with st.expander("🛠️ Chi tiết Tool Calling & Kết quả", expanded=True):
                    for event in tool_events:
                        st.markdown(f"**Tool:** `{event.get('tool')}`")
                        st.json({"args": event.get("args"), "result": event.get("result")})

            if status == "waiting_for_user":
                st.info(f"💡 **Cần thêm thông tin:** {assistant_text}")
            else:
                st.markdown(assistant_text)

            # Ghi nhận vào transcript JSON theo yêu cầu bài lab
            turn_record = {
                "turn_index": st.session_state.turn_index,
                "started_at": start_time,
                "user": prompt,
                "status": status,
                "assistant_text": assistant_text,
                "rounds": loop_result.get("rounds", []),
                "tool_events": tool_events,
                "ended_at": now_iso(),
            }
            st.session_state.transcript["turns"].append(turn_record)
            st.session_state.transcript_path.write_text(
                json.dumps(st.session_state.transcript, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )

            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "tools": tool_events,
                "status": status,
            })
