"""Replay the lab coach's Streamlit test questions through the same loop app.py uses.

Usage (from starter_v0/):
    python scripts/replay_coach_questions.py [--with-send] [analysis/out.json]

Without --with-send the tool list matches the UI default (send hidden).
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from chat import ARTIFACTS_DIR, run_model_tool_loop, trim_history  # noqa: E402
from providers import make_provider  # noqa: E402
from tools import load_tool_declarations, to_openai_tools  # noqa: E402

CASES = {
    "G01_wiki_person": ["Andrej Karpathy là ai?"],
    "G02_news_not_wiki": ["Tin mới nhất về OpenAI trong tuần này"],
    "G03_company_policy": ["Theo quy định của công ty, mình có được trích dẫn một tweet như nguồn đã xác minh không?"],
    "G04_thanks_no_tool": ["Cảm ơn bạn nhiều nhé!"],
    "G05_top_tweets_with_limit": ["Cho mình 7 tweet nổi bật nhất về Claude"],
    "GM01_wiki_switch_language": ["Transformer trong AI là gì?", "Tìm nguồn tiếng Anh giúp mình", "Vẫn chủ đề Transformer đó nhé"],
    "GM02_send_after_confirm": ["Đăng lên Telegram câu này: 'Bản tin AI hôm nay đã sẵn sàng'", "Đúng nội dung đó", "Có, mình xác nhận gửi"],
    "GM03_cancel_send": ["Gửi bản tin này lên Telegram giúp mình", "Khoan đã", "Thôi không gửi nữa, cảm ơn"],
    "GM04_handle_after_clarify": ["Lấy tweet mới nhất giúp mình", "Của Demis Hassabis", "Lấy 4 cái thôi"],
    "GM05_switch_twitter_to_wiki": ["Mọi người nói gì về Anthropic trên Twitter?", "Thôi, mình muốn biết Anthropic là công ty gì", "Tra Wikipedia"],
}

# Same tool list the UI shows by default (send hidden unless UI_ALLOW_SEND=1); pass --with-send to include it.
with_send = "--with-send" in sys.argv
decls = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
if not with_send:
    decls = [d for d in decls if d["name"] != "send"]
tools = to_openai_tools(decls)
system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
provider = make_provider("openrouter")

report = {}
for case_id, turns in CASES.items():
    history: list[dict[str, str]] = []
    log = []
    for user_text in turns:
        messages = [{"role": "system", "content": system_prompt}, *trim_history(history, 5), {"role": "user", "content": user_text}]
        with redirect_stdout(io.StringIO()):
            result = run_model_tool_loop(provider=provider, messages=messages, tools=tools, model=None, max_tool_rounds=4)
        calls = []
        for rnd in result["rounds"]:
            for call, ev in zip(rnd["tool_calls"], rnd["tool_results"]):
                out = ev["result"] if isinstance(ev["result"], dict) else {}
                status = out.get("error") or out.get("status") or (f"{len(out.get('items', out.get('results', [])))} items")
                calls.append({"name": call["name"], "args": call["args"], "result": status})
        log.append({"user": user_text, "status": result["status"], "calls": calls, "answer": result["assistant_text"][:200]})
        history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": result["assistant_text"]}]
    report[case_id] = log

out_path = next((a for a in sys.argv[1:] if a.endswith(".json")), None)
if out_path:
    Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
for case_id, log in report.items():
    print(f"\n=== {case_id}")
    for t in log:
        short = [f"{c['name']}({json.dumps({k: (v[:30] + '…' if isinstance(v, str) and len(v) > 30 else v) for k, v in c['args'].items()}, ensure_ascii=False)})->{c['result']}" for c in t["calls"]]
        print(f"  U: {t['user'][:60]}\n     [{t['status']}] {' ; '.join(short) or 'NO TOOL'}\n     A: {t['answer'][:110]!r}")
