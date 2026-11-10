from __future__ import annotations

from pathlib import Path

import streamlit as st

from chat import ROOT, run_model_tool_loop, trim_history
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools


load_lab_env(ROOT)
ARTIFACTS = ROOT / "artifacts"

st.set_page_config(page_title="Research Agent Lab", page_icon="🧪", layout="wide")
st.title("🧪 Research Agent Lab")
st.caption("Thử agent, kiểm tra tool được chọn và xem kết quả thực thi.")

with st.sidebar:
    st.header("Cấu hình")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini", "ollama"])
    model = st.text_input("Model (để trống dùng mặc định)", placeholder="Ví dụ: qwen2.5:7b")
    version = st.text_input("Nhãn phiên bản", value="v0")
    prompt_file = st.text_input("System prompt", value=str(ARTIFACTS / "system_prompt.md"))
    tools_file = st.text_input("Tool declarations", value=str(ARTIFACTS / "tools.yaml"))
    history_window = st.slider("Số lượt hội thoại giữ trong context", 1, 20, 5)
    max_tool_rounds = st.slider("Số vòng gọi tool tối đa", 1, 8, 4)
    if st.button("Xóa hội thoại", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.history = []

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])
        if item.get("events"):
            with st.expander("Dấu vết gọi tool"):
                for event in item["events"]:
                    st.markdown(f"**{event['tool']}** · `{event['args']}`")
                    st.json(event["result"])

prompt = st.chat_input("Nhập yêu cầu để thử agent…")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            prompt_path = Path(prompt_file).expanduser()
            declaration_path = Path(tools_file).expanduser()
            system_prompt = prompt_path.read_text(encoding="utf-8")
            declarations = load_tool_declarations(declaration_path)
            provider = make_provider(provider_name)
            selected_model = model.strip() or getattr(provider, "default_model", None)
            context = trim_history(st.session_state.history, history_window)
            result = run_model_tool_loop(
                provider=provider,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *context,
                    {"role": "user", "content": prompt},
                ],
                tools=to_openai_tools(declarations),
                model=selected_model,
                max_tool_rounds=max_tool_rounds,
            )
            answer = result["assistant_text"] or "Agent không trả về nội dung văn bản."
            st.markdown(answer)
            if result["tool_events"]:
                with st.expander(f"Dấu vết gọi tool ({len(result['tool_events'])})", expanded=True):
                    for event in result["tool_events"]:
                        st.markdown(f"**{event['tool']}** · `{event['args']}`")
                        st.json(event["result"])
            st.session_state.messages.append({"role": "assistant", "content": answer, "events": result["tool_events"]})
            st.session_state.history.extend([
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer},
            ])
            st.caption(f"Phiên bản {version} · {provider_name} · {selected_model or 'model mặc định'} · {result['status']}")
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            st.error(message)
            st.session_state.messages.append({"role": "assistant", "content": f"Lỗi: {message}"})
