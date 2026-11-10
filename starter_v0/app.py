"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py

Reuses the multi-round tool loop and transcript format from chat.py, and always
reads the current artifacts/system_prompt.md + artifacts/tools.yaml, so the UI
follows whatever version (v0..v3) is checked out.

Safety: the `send` (Telegram) tool is hidden from the model unless the env var
UI_ALLOW_SEND=1 is set, so strangers using the public tunnel link cannot post
to the team's channel.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import ARTIFACTS_DIR, ROOT, now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"
SEND_ENABLED = os.getenv("UI_ALLOW_SEND") == "1"

SAMPLE_QUERIES = [
    "Tin tức AI hôm nay có gì nổi bật?",
    "Tweet mới nhất của Sam Altman là gì?",
    "Tóm tắt bài này giúp mình: https://openai.com/blog/gpt-5",
    "Mọi người đang bàn gì về GPT-5 trên Twitter?",
]


@st.cache_resource(show_spinner=False)
def get_provider(name: str) -> Any:
    return make_provider(name)


def load_tools() -> tuple[list[dict[str, Any]], list[str]]:
    declarations = load_tool_declarations(TOOLS_PATH)
    if not SEND_ENABLED:
        declarations = [item for item in declarations if item["name"] != "send"]
    return to_openai_tools(declarations), [item["name"] for item in declarations]


def new_transcript(provider: str, model: str | None, version: str, history_window: int, max_rounds: int) -> dict[str, Any]:
    artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), "ui", safe_slug(provider), timestamp])
    return {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider,
        "model": model,
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": history_window,
        "max_tool_rounds": max_rounds,
        "source": "streamlit_ui",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def reset_conversation() -> None:
    for key in ("messages", "history", "transcript", "transcript_path"):
        st.session_state.pop(key, None)


def render_tool_events(rounds: list[dict[str, Any]]) -> None:
    for round_record in rounds:
        for event in round_record.get("tool_results", []):
            args = json.dumps(event.get("args", {}), ensure_ascii=False)
            result = event.get("result", {})
            failed = isinstance(result, dict) and "error" in result
            icon = "⚠️" if failed else "🔧"
            with st.expander(f"{icon} vòng {round_record['round']}: {event['tool']}({args})"):
                st.json(result, expanded=False)


def render_message(message: dict[str, Any]) -> None:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            render_tool_events(message.get("rounds", []))
            if message.get("status") == "waiting_for_user":
                st.caption("❓ Agent cần bạn bổ sung thông tin")
            elif message.get("status") == "provider_error":
                st.error(message["content"])
                return
        st.markdown(message["content"] or "_(không có nội dung)_")


# ---------------------------------------------------------------- page
st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")

with st.sidebar:
    st.header("Cấu hình")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    model_input = st.text_input("Model (để trống = mặc định của provider)", value="")
    version = st.text_input("Nhãn version", value="v0")
    history_window = st.slider("Số cặp lượt giữ trong context", 0, 10, 5)
    max_rounds = st.slider("Số vòng tool tối đa mỗi lượt", 1, 6, 4)
    if st.button("Cuộc hội thoại mới", use_container_width=True):
        reset_conversation()
        st.rerun()

    openai_tools, tool_names = load_tools()
    artifact = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    st.divider()
    st.caption(f"artifact_version: `{artifact.artifact_version}`")
    st.caption("Tool đang bật: " + ", ".join(f"`{name}`" for name in tool_names))
    if not SEND_ENABLED:
        st.caption("`send` (Telegram) đang tắt trên UI. Bật bằng biến môi trường `UI_ALLOW_SEND=1`.")
    if "transcript_path" in st.session_state:
        st.caption(f"Transcript: `{Path(st.session_state['transcript_path']).name}`")

st.title("🔎 Research Agent")
st.caption("Tìm tin theo từ khóa hoặc theo tài khoản, đọc URL, tổng hợp nguồn. Agent sẽ hỏi lại khi thiếu thông tin.")

st.session_state.setdefault("messages", [])
st.session_state.setdefault("history", [])

if not st.session_state["messages"]:
    st.markdown("**Thử nhanh:**")
    columns = st.columns(len(SAMPLE_QUERIES))
    for column, sample in zip(columns, SAMPLE_QUERIES):
        if column.button(sample, use_container_width=True):
            st.session_state["pending_input"] = sample
            st.rerun()

for message in st.session_state["messages"]:
    render_message(message)

user_text = st.chat_input("Nhập yêu cầu research...") or st.session_state.pop("pending_input", None)

if user_text:
    model = model_input.strip() or None
    if "transcript" not in st.session_state:
        transcript = new_transcript(provider_name, model, version, history_window, max_rounds)
        st.session_state["transcript"] = transcript
        st.session_state["transcript_path"] = str(TRANSCRIPTS_DIR / f"{transcript['transcript_id']}.transcript.json")
    transcript = st.session_state["transcript"]

    user_message = {"role": "user", "content": user_text}
    st.session_state["messages"].append(user_message)
    render_message(user_message)

    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state["history"], history_window),
        {"role": "user", "content": user_text},
    ]
    turn_record: dict[str, Any] = {
        "turn_index": len(transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.spinner("Agent đang xử lý..."):
        try:
            result = run_model_tool_loop(
                provider=get_provider(provider_name),
                messages=messages,
                tools=openai_tools,
                model=model,
                max_tool_rounds=max_rounds,
            )
            turn_record.update(result)
            assistant_message = {
                "role": "assistant",
                "content": result["assistant_text"],
                "status": result["status"],
                "rounds": result["rounds"],
            }
            st.session_state["history"].append({"role": "user", "content": user_text})
            st.session_state["history"].append({"role": "assistant", "content": result["assistant_text"]})
        except Exception as exc:  # show provider/config errors instead of crashing the page
            error = f"{type(exc).__name__}: {exc}"
            turn_record.update({"status": "provider_error", "error": error})
            assistant_message = {"role": "assistant", "content": error, "status": "provider_error", "rounds": []}

    turn_record["ended_at"] = now_iso()
    transcript["turns"].append(turn_record)
    write_transcript(Path(st.session_state["transcript_path"]), transcript)

    st.session_state["messages"].append(assistant_message)
    render_message(assistant_message)
