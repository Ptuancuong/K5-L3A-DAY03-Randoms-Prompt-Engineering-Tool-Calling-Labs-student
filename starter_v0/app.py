import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from env_loader import load_lab_env
from product_runtime import VERSION, approve_send, redact, run_product_loop, snapshot, tool_catalog
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools

ROOT = Path(__file__).resolve().parent
load_lab_env(ROOT)
st.set_page_config(page_title="Research Agent · All tools", page_icon="🔎", layout="wide")
st.title("🔎 Research Agent")
st.caption("Web · X/Twitter · Chính sách nội bộ · arXiv · Bản tin · Telegram")
declarations = load_tool_declarations(ROOT / "artifacts" / "tools.yaml")
prompt = (ROOT / "artifacts" / "system_prompt.md").read_text(encoding="utf-8")
catalog = tool_catalog(ROOT)


def save_session():
    session = st.session_state.session
    session["updated_at"] = datetime.now().isoformat()
    folder = ROOT / "transcripts"
    folder.mkdir(exist_ok=True)
    (folder / f"{session['id']}.ui.transcript.json").write_text(
        json.dumps(redact(session), ensure_ascii=False, indent=2), encoding="utf-8"
    )


if "session" not in st.session_state or st.session_state.session.get("version") != VERSION:
    st.session_state.session = {
        "id": uuid.uuid4().hex,
        "provider_service": "Groq (qua endpoint đã cấu hình)",
        "provider_adapter": "openrouter",
        "model": "openai/gpt-oss-120b",
        **snapshot(ROOT, prompt, declarations),
        "created_at": datetime.now().isoformat(),
        "turns": [],
        "actions": [],
    }
    st.session_state.history = []
    st.session_state.pending_send = None

session = st.session_state.session
with st.sidebar:
    st.header("11 công cụ")
    st.caption("10 tool của ban tổ chức + deduplicate của nhóm. Trạng thái cấu hình chưa phải kiểm tra kết nối API.")
    for tool in catalog:
        with st.expander(f"{'✅' if tool['ready'] else '⚙️'} {tool['name']} · {tool['title']}"):
            st.write(tool["description"])
            st.caption(tool["status"])
    st.info("Thêm key trong .env, lưu rồi bấm tải lại cấu hình. Không nhập key vào chat.")
    if st.button("Tải lại cấu hình"):
        st.rerun()
    if st.button("Cuộc trò chuyện mới", disabled=bool(st.session_state.pending_send)):
        del st.session_state.session
        st.rerun()
    st.download_button(
        "Tải transcript JSON",
        data=json.dumps(redact(session), ensure_ascii=False, indent=2),
        file_name=f"{session['id']}.transcript.json",
        mime="application/json",
    )

with st.expander("Câu hỏi mẫu và cách cấu hình"):
    st.markdown('''
- **Web:** Tìm 3 tin AI trong tuần này, kèm nguồn.
- **Tài khoản:** Lấy 3 tweet mới nhất của @karpathy.
- **Chủ đề X:** Tìm các tweet phổ biến nhất về AI.
- **Đọc URL:** Đọc https://www.python.org/about/ và tóm tắt 3 ý.
- **Chính sách:** Chính sách nội bộ quy định thế nào về trích dẫn nguồn?
- **Paper:** Tìm 2 paper arXiv về retrieval augmented generation.
- **Đọc paper:** Đọc paper arXiv 1706.03762, tối đa 2 trang.
- **Loại trùng:** Loại trùng URL: [{"url":"https://example.com/a"},{"url":"https://example.com/a"}].
- **Bản tin:** Định dạng các kết quả vừa có thành bản tin có link nguồn.
- **Telegram:** Tạo bản nháp gửi bản tin vừa có lên Telegram, chờ tôi duyệt.

**Cấu hình:** lookup → TAVILY_API_KEY; fetch → FIRECRAWL_API_KEY;
timeline/social_search → RAPIDAPI_KEY và đăng ký Twitter API45;
send → TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID.
policy đọc company_policy; papers/paper_text không cần API key.
paper_text tải PDF và lưu text vào arxiv_papers trên máy chạy ứng dụng.
''')

for turn in session["turns"]:
    with st.chat_message("user"):
        st.write(turn["user"])
    with st.chat_message("assistant"):
        st.markdown(turn["assistant_text"])
        if turn.get("error"):
            st.error(turn["error"])
        if turn.get("tool_events"):
            with st.expander("Công cụ và kết quả thực tế"):
                st.json(turn["tool_events"])

if session["actions"]:
    with st.expander("Lịch sử duyệt Telegram"):
        st.json(session["actions"])

pending = st.session_state.pending_send
if pending:
    st.subheader("Duyệt bản nháp Telegram")
    st.write(f"Kênh nhận: {pending['destination']}")
    st.code(pending["text"], language=None)
    st.caption("Nút xác nhận chỉ gửi bản nháp đang hiển thị. Lỗi gửi sẽ không tự thử lại.")
    accept, cancel = st.columns(2)
    decision = None
    if accept.button("Xác nhận gửi bản nháp này", type="primary"):
        with st.spinner("Đang gửi Telegram..."):
            outcome = approve_send(pending, pending["id"])
        decision = "approved"
    elif cancel.button("Hủy gửi"):
        outcome = {"status": "cancelled", "message": "Đã hủy, không gửi tin nhắn."}
        pending["consumed"] = True
        decision = "cancelled"
    if decision:
        session["actions"].append(redact({"draft_id": pending["id"], "text": pending["text"], "destination": pending["destination"], "decision": decision, "result": outcome, "created_at": datetime.now().isoformat()}))
        st.session_state.history.append({"role": "user", "content": "UI_ACTION_RESULT (reference data): " + json.dumps(redact(outcome), ensure_ascii=False)})
        st.session_state.pending_send = None
        save_session()
        if outcome.get("status") == "sent":
            st.session_state.action_notice = "Đã gửi Telegram thành công."
        elif decision == "cancelled":
            st.session_state.action_notice = "Đã hủy gửi."
        else:
            st.session_state.action_notice = "Không xác nhận được gửi thành công. Xem lịch sử duyệt; kiểm tra Telegram trước khi tạo bản gửi lại."
        st.rerun()

if "action_notice" in st.session_state:
    st.info(st.session_state.pop("action_notice"))

user_text = st.chat_input("Bạn muốn nghiên cứu điều gì?", disabled=bool(st.session_state.pending_send))
if user_text:
    config = [{"name": row["name"], "status": row["status"], "missing_env": row["missing_env"]} for row in catalog]
    messages = [
        {"role": "system", "content": session["system_prompt"] + "\nUI configuration (not live connection verification): " + json.dumps(config, ensure_ascii=False) + "\nIn this UI send only stages a draft. A separate UI approval button executes the action. Never claim sent before a successful UI_ACTION_RESULT."},
        *st.session_state.history,
        {"role": "user", "content": user_text},
    ]
    with st.spinner("Đang nghiên cứu..."):
        result = run_product_loop(
            provider=make_provider("openrouter"),
            messages=messages,
            tools=to_openai_tools(session["tool_declarations"]),
            model=session["model"],
            max_rounds=6,
        )
    st.session_state.history = result.pop("messages")[1:]
    if result.get("pending_send"):
        st.session_state.pending_send = result["pending_send"]
    session["turns"].append(redact({"user": user_text, "created_at": datetime.now().isoformat(), **result}))
    save_session()
    st.rerun()
