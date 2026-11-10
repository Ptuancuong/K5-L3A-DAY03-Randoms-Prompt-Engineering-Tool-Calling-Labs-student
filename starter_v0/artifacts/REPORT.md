# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
>
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: ____
- Members: Cường (bản này: làm đủ cả 5 vai), ____
- Provider/model: OpenRouter — `openai/gpt-4o-mini`, temperature 0

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent cho tin tức AI/công nghệ: tìm tin trên web, xem tweet theo tài khoản hoặc theo chủ đề, đọc một URL, tra Wikipedia, Hacker News, GitHub, Hugging Face, rồi tổng hợp có nguồn. Agent **hỏi lại khi thiếu thông tin** (thiếu tài khoản, thiếu link) và **hỏi xác nhận trước khi đăng lên Telegram**.

**Link dùng thử (deploy):**

> URL: ____ (Streamlit `app.py` + Cloudflare Tunnel — điền khi mở tunnel)

## A2. Tool agent có

| Tên tool                     | Làm được gì                                                                            | Tool mới nhóm thêm? |
| ---------------------------- | -------------------------------------------------------------------------------------- | ------------------- |
| clarify                      | Hỏi lại người dùng khi thiếu tài khoản/URL, hoặc xác nhận yes/no trước khi gửi         | không               |
| timeline                     | Lấy tweet mới nhất của MỘT tài khoản X/Twitter (map tên → handle: Sam Altman → `sama`) | không               |
| social_search                | Tìm tweet VỀ một chủ đề (Latest hoặc Top)                                              | không               |
| lookup                       | Tìm trên web / tin tức (Tavily), có `topic=news` và `timeframe` day/week/month/year    | không               |
| fetch                        | Đọc nội dung một URL cụ thể (Firecrawl)                                                | không               |
| format                       | Trình bày các item đã có thành digest markdown                                         | không               |
| send                         | Đăng lên Telegram — chỉ khi user đã xác nhận (`confirmed=true`)                        | không (bonus)       |
| policy / papers / paper_text | Tra policy nội bộ, tìm paper arXiv, đọc text paper arXiv                               | không (bonus)       |
| **wiki**                     | Tóm tắt bài Wikipedia về một khái niệm / người / tổ chức (en, vi)                      | **có**              |
| **hn_search**                | Tìm bài trên Hacker News (theo độ liên quan hoặc mới nhất)                             | **có**              |
| **github_search**            | Tìm repo GitHub, lọc ngôn ngữ, sắp theo sao / mới cập nhật                             | **có**              |
| **hf_models**                | Tìm model trên Hugging Face theo từ khóa hoặc tác vụ (vd. text-to-speech)              | **có**              |

## A3. Câu hỏi mẫu để thử

1. `Tin tức AI hôm nay có gì nổi bật?` → web news hôm nay
2. `Tóm tắt 3 tweet mới nhất của Andrej Karpathy` → timeline `karpathy`, 3 tweet
3. `Model text-to-speech nào trên Hugging Face được tải nhiều nhất?` → hf_models
4. `Tìm repo GitHub viết bằng Rust về vector database, nhiều sao nhất` → github_search
5. `Tóm tắt bài viết này hộ mình` (không kèm link) → agent hỏi lại link

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: `artifacts/version_log.csv`, `runs/*.json`. Metric = `case_accuracy` trên base eval (20 case); group eval (10 case) chạy từ v2.

| Version | Changed Artifact   | Hypothesis                                                                                                                                                          |                            Metric Before |                                                                                                                                                                                                                Metric After | Run File                                                                                                                                                                           |
| ------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| v0      | baseline           | Prompt starter khuyến khích đoán / tự gửi / một bước → các case clarify, confirm, no-tool sẽ fail                                                                   |                                        – |                                                                                                                                                                          base 0.65 (routing 0.75, args 0.65, multiturn 1.0) | `runs/v0_B_base_openrouter_20261110T111636289678.json`                                                                                                                             |
| v1      | `system_prompt.md` | Bỏ 3 chỉ dẫn xấu + thêm ranh giới hành vi (clarify khi thiếu tài khoản/URL, xác nhận trước khi gửi, không tool cho câu meta/ngoài phạm vi, cho phép gọi nhiều tool) |                                     0.65 |                                                                                                                                                                                   base **0.95** (routing 1.0) — chỉ còn R12 | `runs/v1_B_base_openrouter_20261110T111827291351.json`                                                                                                                             |
| v2      | `tools.yaml`       | Description có khi nào dùng / không dùng + quy ước args (clarify `yes_no` cho gửi, query ngắn, topic/timeframe, handle không `@`); khai báo 4 tool mới cùng chuẩn   |                                     0.95 |                                                                                                                                                   base 0.95 (R12 sửa được, **M06 tụt**: gọi thừa social_search); group 0.80 | `runs/v2_B_base_openrouter_20261110T112535857722.json`, `runs/v2_B_group_openrouter_20261110T112703896909.json`                                                                    |
| v3      | `system_prompt.md` | Rule nhiều lượt: gộp các lượt thành một yêu cầu hiện tại, lượt sau ghi đè, nguồn đã "bỏ/chuyển" thì không gọi lại                                                   |                   base 0.95 / group 0.80 |                                                                                                                        base 0.95 (multiturn 1.0, M06 sửa được; R12 lại dao động sang `text`); group **0.90** (G08 sửa được) | `runs/v3_B_base_openrouter_20261110T112827808401.json`, `runs/v3_B_group_openrouter_20261110T112852474002.json`                                                                    |
| v4      | `system_prompt.md` | Live chat v3: sau "Có, đăng đi" model gọi `send` thiếu `confirmed=true`. Thêm rule bắt buộc gửi `confirmed=true` sau khi user đồng ý                                |                   base 0.95 / group 0.90 |                                                              base 0.95; group 1.0 (G07 cũng PASS dù không nhắm tới → nhiều khả năng do dao động). **Live chat vẫn thiếu `confirmed=true` → giả thuyết KHÔNG được xác nhận** | `runs/v4_B_base_openrouter_20261110T114020020965.json`, `runs/v4_B_group_openrouter_20261110T114041423746.json`, `transcripts/v4_openrouter_20261110T114057873833.transcript.json` |
| v5      | `system_prompt.md` | Câu coach GM01: lượt "Vẫn chủ đề Transformer đó nhé" bỏ `wiki` chuyển sang lookup + social_search. Thêm rule: lượt chỉ chỉnh tiếp thì giữ nguyên tool cũ            |                    base 0.95 / group 1.0 | base 0.95; group 0.90 (G07 lại FAIL — dao động). **GM01 vẫn FAIL → giả thuyết KHÔNG được xác nhận.** Nguyên nhân gốc: lịch sử hội thoại trong `chat.py`/`app.py` chỉ lưu text, model không thấy lượt trước đã dùng tool nào | `runs/v5_B_base_openrouter_20261110T121254491717.json`, `runs/v5_B_group_openrouter_20261110T121318731405.json`                                                                    |
| v6      | `system_prompt.md` | Câu coach: 5/17 câu trả lời cho câu hỏi tiếng Việt lại viết bằng tiếng Anh. Thêm rule: luôn trả lời theo ngôn ngữ của user                                          | base 0.95 / group 0.90; tiếng Việt 12/17 |                                      base 0.95; group 0.90; **tiếng Việt 17/17 → giả thuyết được xác nhận.** Tác dụng phụ: model hay chọn `wiki(lang=vi)` hơn → G01 không có bài tiếng Việt (đã sửa bằng code tool, xem B5) | `runs/v6_B_base_openrouter_20261110T121705868044.json`, `runs/v6_B_group_openrouter_20261110T121731555224.json`, `analysis/coach_replay_v6_wikifix.json`                           |

### B1b. Bộ câu test của lab coach (chạy qua đúng vòng lặp của Streamlit)

`scripts/replay_coach_questions.py` chạy 10 câu của coach qua `run_model_tool_loop` (cùng vòng lặp `app.py` dùng, lịch sử hội thoại thật, `send` bật). Kết quả: `analysis/coach_replay_v4.json` → `analysis/coach_replay_v6_wikifix.json`.

| Case                        | v4              | v6 + fix `wiki` | Ghi chú                                                                                                                            |
| --------------------------- | --------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| G01_wiki_person             | ✅              | ✅              | v6 chọn `lang=vi`, tool tự fallback sang bài tiếng Anh                                                                             |
| G02_news_not_wiki           | ✅ (trả lời EN) | ✅              | `lookup(OpenAI, news, week)`                                                                                                       |
| G03_company_policy          | ✅              | ✅              | `policy(source_citation)`                                                                                                          |
| G04_thanks_no_tool          | ✅              | ✅              | Không tool                                                                                                                         |
| G05_top_tweets_with_limit   | ✅ (trả lời EN) | ✅              | `social_search(Claude, Top, 7)`                                                                                                    |
| GM01_wiki_switch_language   | ❌              | ❌              | Lượt 1 đã có kết quả; lượt 2–3 vẫn đổi tool (lookup/papers) — model không thấy tool của lượt trước                                 |
| GM02_send_after_confirm     | ⚠️              | ⚠️              | Gửi `confirmed=true` ngay ở lượt "Đúng nội dung đó" rồi gửi lại ở lượt 3 (gửi lặp). Telegram chưa cấu hình nên không có tin nào đi |
| GM03_cancel_send            | ✅              | ✅              | Không gửi                                                                                                                          |
| GM04_handle_after_clarify   | ✅              | ✅              | `clarify` → `timeline(demishassabis)` → limit 4                                                                                    |
| GM05_switch_twitter_to_wiki | ✅              | ✅              | `social_search` → `wiki(Anthropic)`                                                                                                |

## B2. Failure Analysis

Từ `results[*].result.failures` của các run trên.

| Case ID                             | Failure Type     | Actual Tool Calls                                             | What Failed                                        | Fix                                                                   |
| ----------------------------------- | ---------------- | ------------------------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------- |
| R10_missing_handle (v0)             | missing_info     | `timeline(screenname="sama")`                                 | Đoán tài khoản thay vì hỏi                         | v1: thiếu tài khoản → `clarify(text)`                                 |
| R11_missing_url (v0)                | missing_info     | `fetch(url="https://example.com/article")`                    | Bịa URL                                            | v1: thiếu link → `clarify(text)`, không bịa URL                       |
| R12_confirm_before_send (v0)        | wrong_boundary   | `send(text="Bản tin này")`                                    | Gửi ngay, không xác nhận                           | v1: xác nhận trước khi gửi                                            |
| R08 / R14 out_of_scope (v0)         | out_of_scope     | `send(text=<lời giải toán / code>)`                           | Dùng `send` để trả lời câu ngoài phạm vi           | v1: câu ngoài phạm vi → không tool; không dùng `send` để trả lời      |
| R03_web_news_routing (v0)           | wrong_arg_value  | `lookup(query="AI news", …)`                                  | `query` bị thêm chữ "news"                         | v1 tự hết (không còn ép một bước); v2 ghi quy ước query ngắn          |
| R13_parallel (v0)                   | wrong_arg_value  | `lookup(query="AI news", không topic)` + `social_search`      | Thiếu `topic=news`, query sai                      | v1 (cho phép nhiều tool) + v2 (quy ước topic)                         |
| R12 (v1, v3)                        | wrong_boundary   | `clarify(response_type="text", "Bạn muốn đăng nội dung gì?")` | Hỏi nội dung thay vì yes/no                        | v2: mô tả `response_type` — sửa được ở v2 nhưng **dao động lại ở v3** |
| M06_switch_tool (v2)                | wrong_tool       | `lookup(OpenAI, news)` + `social_search(OpenAI)`              | Lượt 2 đã "bỏ Twitter" nhưng vẫn gọi social_search | v3: rule nguồn đã bỏ không gọi lại                                    |
| M_G08_switch_web_to_hn (v2)         | wrong_tool       | `lookup(Rust)` + `hn_search(Rust)`                            | Chuyển sang HN nhưng vẫn gọi web                   | v3 (sửa được)                                                         |
| M_G07_drop_source_persists (v2, v3) | unnecessary_tool | `lookup(AI, news, day)` + `social_search(AI)`                 | Lượt 2 "bỏ Twitter", lượt 3 vẫn gọi social_search  | **Chưa sửa được** ở v3                                                |

## B3. Team Eval Cases

`data/eval_group.json` — 5 single turn + 5 multi turn; 6 case gọi tool mới. Kết quả v2 → v3.

| Case ID                          | What It Tests                                                          | Expected Tool/Behavior                           | Result (v2 → v3) |
| -------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------ | ---------------- |
| G01_wiki_concept_routing         | Hỏi định nghĩa → wiki, không lookup                                    | `wiki`                                           | PASS → PASS      |
| G02_hn_routing_query             | Nhắc Hacker News → hn_search, query ngắn                               | `hn_search(query="Rust")`                        | PASS → PASS      |
| G03_github_language_sort         | Ngôn ngữ vào arg `language`, "nhiều sao" → stars                       | `github_search(language="Python", sort="stars")` | PASS → PASS      |
| G04_hf_task_arg                  | Tác vụ → `task=text-to-speech`, tải nhiều → downloads                  | `hf_models(task, sort)`                          | PASS → PASS      |
| G05_news_about_hf_is_lookup      | Tin tức VỀ Hugging Face → lookup, không hf_models (ranh giới tool mới) | `lookup(query="Hugging Face", news, day)`        | PASS → PASS      |
| M_G06_confirm_then_send          | Đã xác nhận "Có" → `send(confirmed=true)`                              | `send(confirmed=true)`                           | PASS → PASS      |
| M_G07_drop_source_persists       | Bỏ Twitter ở lượt 2 → lượt 3 chỉ lookup (lấy từ lỗi M06)               | `lookup(AI, news, day)` only                     | FAIL → FAIL      |
| M_G08_switch_web_to_hn           | Đổi web → Hacker News, giữ chủ đề                                      | `hn_search(query="Rust")` only                   | FAIL → PASS      |
| M_G09_github_language_correction | Sửa Python → Rust, giữ sort                                            | `github_search(language="Rust", sort="stars")`   | PASS → PASS      |
| M_G10_clarify_then_wiki          | Bổ sung khái niệm sau khi được hỏi → wiki                              | `wiki`                                           | PASS → PASS      |

## B4. Live Chat Evidence

`transcripts/v3_openrouter_20261110T113230259751.transcript.json` — `chat.py`, artifact `v3+p76efdf4aa816+tc8e152203f1a`.

| Turn | User Request                                        | Tool Calls                                          | Version Evidence | Outcome                                                                                                |
| ---- | --------------------------------------------------- | --------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------ |
| 1    | Tin tức AI hôm nay có gì nổi bật?                   | `lookup(query="AI", topic="news", timeframe="day")` | v3               | Đúng; trả 5 tin có nguồn (nhưng trả lời bằng tiếng Anh)                                                |
| 2    | Tóm tắt 3 tweet mới nhất giúp mình                  | `social_search(query="AI", limit=3)`                | v3               | **Cần review**: không hỏi tài khoản mà suy chủ đề "AI" từ lượt 1                                       |
| 3    | Của Andrej Karpathy nhé                             | `timeline(screenname="karpathy", limit=3)`          | v3               | Đúng: map tên → handle, giữ limit=3                                                                    |
| 4    | Wikipedia nói gì về Retrieval-augmented generation? | `wiki(title="Retrieval-augmented generation")`      | v3               | Đúng, tool mới được route đúng                                                                         |
| 5    | Đăng bản tin AI hôm nay lên Telegram giúp mình      | `clarify(response_type="yes_no")`                   | v3               | Đúng: hỏi xác nhận, không gửi                                                                          |
| 6    | Có, đăng đi                                         | `send(text=…)` **thiếu `confirmed=true`**           | v3               | **Lỗi model**: tool guardrail trả `needs_confirmation`, agent hỏi lại lần nữa. Không có tin nào bị gửi |

Kiểm tra lại sau v4 (`transcripts/v4_openrouter_20261110T114057873833.transcript.json`): `lookup` → `clarify(yes_no)` → sau "Có, đăng đi" vẫn `send(text=…)` **không có `confirmed=true`** → lỗi còn nguyên, guardrail trong code vẫn chặn.

## B5. Bonus Evidence

| Bonus                                  | Evidence File                                                             | What Worked                                                                                                | Risk / Guardrail                                                                                                                                             |
| -------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| send (Telegram)                        | base R12, group M_G06, transcript turn 5–6                                | Hỏi yes/no trước khi gửi; sau khi xác nhận, eval G06 gọi `send(confirmed=true)`                            | Live chat turn 6 model quên `confirmed=true` → guardrail trong code chặn. UI ẩn `send` trừ khi `UI_ALLOW_SEND=1` để người lạ qua link public không đăng được |
| arXiv/company policy                   | `tools.yaml` (mô tả policy_area, papers, paper_text)                      | Đã viết lại description; chưa chạy suite extension                                                         | —                                                                                                                                                            |
| UI                                     | `app.py` (Streamlit)                                                      | Chat nhiều lượt, hiện tool calls + args + kết quả, lưu transcript vào `transcripts/`                       | Không hiện key/env; `send` tắt mặc định                                                                                                                      |
| 4 tool mới (bonus point: UI + >3 tool) | `tools/wiki`, `tools/hn_search`, `tools/github_search`, `tools/hf_models` | Đủ `TOOL.md`, đăng ký `TOOL_FUNCTIONS` + `tools.yaml`; route đúng 6/6 case liên quan (v3)                  | Không cần API key; GitHub không token bị giới hạn 10 lần/phút                                                                                                |
| Tool unit tests (`tests/`)             | `pytest` output: **119 passed, 0 skipped, 0 failed**                      | 21 test cho 4 tool mới (gồm 2 test cho fallback của `wiki`); 14 stub challenge đã điền + 2 test regression | Toàn bộ offline (mock HTTP)                                                                                                                                  |

**Fix code tool `wiki` (không đổi prompt/tools.yaml):** sau v6 model hay chọn `lang=vi`, mà nhiều bài (vd. "Andrej Karpathy", "Transformer (deep learning)") không có trên Wikipedia tiếng Việt → 0 kết quả. Tool giờ tìm theo thứ tự: đúng tên → Wikipedia title search → nếu `vi` không có thì lấy bản `en` (trả `requested_lang`, `note`). Đây là lỗi eval không bắt được (eval chỉ chấm model gọi `wiki` đúng, không chấm kết quả rỗng).

Tool unit tests: 37 test trong `tests/test_tools_todo.py` (21 cho tool mới, 16 cho tool có sẵn). **Tìm được 2 bug trong tool có sẵn** (`timeline` và `social_search`, hàm `_tweets_from`):

1. `limit` âm (vd. `-3`) → code `items[: int(limit or 5)]` cắt thành `items[:-3]`, trả về "tất cả trừ 3 cái cuối" thay vì số mặc định.
2. `limit="three"` → `int("three")` raise `ValueError`, làm hỏng cả lượt gọi tool.

Đã sửa bằng `clamp_int(limit, 5, 0, 100) or 5` và giữ 2 test regression. Đây là lỗi mà **eval không bắt được**: eval chỉ kiểm tra model gửi `limit` đúng; nếu model gửi giá trị lạ thì code tool mới là chỗ hỏng. Lưu ý khi viết test: bản đầu dùng `limit=-1` PASS do trùng hợp (6 tweet bỏ 1 = 5 = mặc định), phải đổi sang `-3` thì test mới thật sự bắt được bug.

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** hành vi và ranh giới (hỏi lại thay vì đoán, xác nhận trước khi gửi, không tool cho câu ngoài phạm vi, rule nhiều lượt). v1 một mình đưa base từ 0.65 → 0.95.
- **Fix thuộc `tools.yaml`:** quy ước tham số và ranh giới giữa các tool (`response_type=yes_no` cho gửi, query ngắn, topic/timeframe, khi nào dùng tool mới thay vì `lookup`). Thêm 4 tool không làm tụt routing của case một lượt, nhưng mô tả dài hơn làm lộ ra lỗi nhiều lượt (M06) → phải sửa ở prompt (v3).
- **Cần review thủ công:** R12 — câu "Đăng bản tin này" không có nội dung bản tin, hỏi lại nội dung (`text`) cũng là hành vi hợp lý; kết quả dao động giữa các version dù temperature 0. Live chat turn 2 (suy chủ đề từ lượt trước thay vì hỏi tài khoản) cũng là vùng xám mà eval tự động không chấm.
- **Eval tự động không bắt được lỗi `confirmed`:** case G06 PASS ở cả v2–v4 (eval gộp các lượt thành một tin nhắn), nhưng live chat thật (lịch sử hội thoại dạng nhiều message) thì model bỏ `confirmed=true`. Rule trong prompt (v4) không đủ; hướng tiếp theo là sửa schema trong `tools.yaml` (đưa `confirmed` vào `required`) — đây là chỗ guardrail trong code (`send` từ chối khi chưa xác nhận) chứng minh giá trị.
- **Không phải lỗi nào cũng sửa được bằng prompt:** GM01 (v5) thất bại vì lịch sử hội thoại của harness chỉ có text, không có tool call; lỗi `wiki` trả rỗng là lỗi code tool. Cả hai chỉ lộ ra khi chạy bộ câu của coach qua vòng lặp chat thật, eval gộp lượt không thấy.
- **Cải thiện tiếp:** (1) lưu tóm tắt tool call vào lịch sử chat để lượt sau biết đang dùng tool nào (GM01); (2) chống gửi lặp và chỉ gửi sau một câu "có" rõ ràng (GM02); (3) `confirmed` bắt buộc trong schema `send`; (4) G07, R12 dao động giữa các lần chạy — nên chạy mỗi version nhiều lần thay vì tin một lần.

## B7. Small Local Model Challenge (bonus)

Nhóm không làm phần này.
