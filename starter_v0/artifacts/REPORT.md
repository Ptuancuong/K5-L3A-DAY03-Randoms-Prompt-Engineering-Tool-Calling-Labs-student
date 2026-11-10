# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: Randoms
- Members: 4
- Provider/model: openai/gpt-oss-120b`, chạy trên Groq.

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

Research Agent hỗ trợ tìm kiếm thông tin trên web và mạng xã hội theo từ khóa hoặc tài khoản, đọc nội dung từ URL và tổng hợp thành bản tin ngắn gọn. Agent hỏi lại khi thiếu thông tin và chỉ gửi bản tin lên Telegram sau khi người dùng xác nhận.

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: Chưa triển khai 

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại khi thiếu thông tin hoặc cần xác nhận | Không |
| timeline | Lấy bài đăng gần đây của một tài khoản X/Twitter | Không |
| social_search | Tìm bài đăng X/Twitter theo chủ đề, mới nhất hoặc phổ biến | Không |
| lookup | Tìm kiếm thông tin và tin tức trên web bằng Tavily | Không |
| fetch | Đọc nội dung URL bằng Firecrawl | Không |
| format | Định dạng dữ liệu đã có thành bản tin Markdown | Không |
| send | Tạo bản nháp Telegram; gửi sau khi người dùng duyệt trên UI | Không |
| policy | Tra cứu chính sách nội bộ trong company_policy | Không |
| papers | Tìm bài báo khoa học trên arXiv | Không |
| paper_text | Tải PDF arXiv và trích xuất nội dung văn bản | Không |
| deduplicate | Loại item trùng URL, giữ bản đầu tiên và thứ tự | Có |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tìm trên web 3 tin tức về năng lượng tái tạo trong tuần này, tổng hợp ngắn gọn và kèm link nguồn.
2. Đọc https://www.python.org/about/ và tóm tắt bằng tiếng Việt thành 3 ý, kèm URL nguồn.
3. Đọc và tóm tắt bài viết này giúp tôi. (Kiểm tra agent có hỏi xin URL.)
4. Tìm 8 tin về pin mặt trời trong tháng này; ở lượt sau đổi thành 2 kết quả và giữ các yêu cầu khác.
5. Dùng deduplicate loại trùng URL: `[{"title":"A","url":"https://example.com/a"},{"title":"A copy","url":"https://example.com/a"},{"title":"B","url":"https://example.com/b"}]`.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo bản starter chưa chỉnh sửa | N/A | case_accuracy=65% | runs/v0_B_base_openrouter_20261110T102244648165.json |
| v1 | system_prompt.md | Hỏi lại khi thiếu tài khoản hoặc URL thay vì tự đoán | 65% | 80% | runs/v1_B_base_openrouter_20261110T103821766936.json |
| v2 | tools.yaml | Tách chủ đề query khỏi topic và timeframe | 80% | 85% | runs/v2_B_base_openrouter_20261110T104636492570.json |
| v3 | system_prompt.md | Thêm quy tắc xác nhận trước khi gửi; R12 vẫn chưa đạt | 85% | 85% |runs/v3_B_base_openrouter_20261110T105953711002.json |



## B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R01 — v0 | wrong_arg_value | timeline(screenname="SamAltman", limit=1) | Sai handle; expected "sama" | v1 dùng đúng "sama"; chưa đủ bằng chứng quy cải thiện này cho riêng rule hỏi lại |
| R03 — v0/v3 | wrong_arg_value | lookup(query="AI news today", topic="news", timeframe="day") | Query không khớp expected "AI" | v2 làm rõ convention query trong tools.yaml; case vẫn chưa đạt ở v3 |
| R10 — v0 | missing_tool_call | timeline(screenname="sama", limit=5) | Tự chọn tài khoản khi người dùng chưa cung cấp; thiếu clarify | v1 thêm rule hỏi tài khoản; case đạt |
| R11 — v0 | missing_tool_call | lookup(query="OpenAI GPT-4 Turbo release article summary") | Tự tìm bài khác khi thiếu URL; thiếu clarify | v1 thêm rule hỏi xin URL; case đạt |
| R12 — v0 | wrong_boundary | send(confirmed=true) với nội dung tự tạo | Gọi gửi khi chưa được xác nhận; gửi thật thất bại do thiếu cấu hình | v3 thêm quy tắc xác nhận; không còn gọi send ở case này nhưng vẫn chưa đạt expected yes_no |
| R12 — v3 | wrong_arg_value | clarify(response_type="text") | Expected response_type="yes_no" nhưng agent hỏi xin nội dung/kênh bằng text | Chưa đạt trong base eval v3; v5 bổ sung duyệt bản nháp bằng nút UI, chưa chạy lại base |
| R13 — v3 | missing_tool_call | lookup(query="AI", topic="news", timeframe="day") | Yêu cầu cả web và Twitter nhưng thiếu social_search | v5 bỏ rule ép một tool và bổ sung routing nhiều nguồn; chưa chạy lại base để xác minh |
| M02 — v0/v1 | wrong_arg_value | lookup(query="robotics news today", topic="news", timeframe="day") | Query không khớp expected "robotics" | v2 tách chủ đề khỏi loại tin/thời gian; case đạt |
| G07 — v3-deduplicate | missing_tool_call | social_search(query="pin mặt trời", limit=2, search_type="Latest") | Đổi sai nguồn từ web sang Twitter khi người dùng chỉ sửa số lượng | v4 thêm rule giữ ràng buộc cũ; gọi đúng lookup(max_results=2, topic="news", timeframe="month"), case đạt |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01 | Loại tin trùng URL | deduplicate | PASS |
| G02 | Tin tuần này, đúng số lượng | lookup | PASS |
| G03 | Đọc URL cụ thể | fetch | PASS |
| G04 | Thiếu URL | clarify | PASS |
| G05 | Giới thiệu khả năng | Không gọi tool | PASS |
| G06 | Bổ sung URL sau khi hỏi | fetch | PASS |
| G07 | Sửa số lượng, giữ nguồn và thời gian | lookup | FAIL ở v3-deduplicate; PASS ở v4-context |
| G08 | Sửa URL | fetch với URL mới | PASS |
| G09 | Loại trùng dữ liệu ở lượt trước | deduplicate | PASS |
| G10 | Chuyển từ tìm kiếm sang đọc URL | fetch | PASS |

v4-context đạt 10/10 case nhóm, tăng từ 90% lên 100%.
Quy tắc giữ các ràng buộc không bị thay đổi đã sửa G07:
lookup(max_results=2, topic=news, timeframe=month).
Evidence: runs/v4-context_B_group_openrouter_20261110T113602688997.json

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

Transcript: `transcripts/v4-context_openrouter_20261110T115557837995.transcript.json`
Version: `v4-context+pf57c5e87e336+taf94849ae081`

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tìm 3 tin năng lượng tái tạo trong tuần | lookup → format | v4-context | Trả 3 tin với link nguồn |
| 2 | Đọc bài nhưng chưa cung cấp URL | clarify | v4-context | Hỏi xin URL, không tự đoán |
| 3 | Cung cấp URL python.org/about | Không lưu được bước trung gian của lượt lỗi | v4-context | Provider trả 400: arguments không đúng JSON |
| 4 | Yêu cầu đọc lại URL, tóm tắt trực tiếp | fetch | v4-context | Tóm tắt thành công bằng tiếng Việt, kèm URL |
| 5 | Loại tin trùng URL | deduplicate | v4-context | Nhận 3 item, giữ 2, loại 1 item trùng |

Lượt 3 gặp lỗi JSON arguments từ provider. Khi thử lại với yêu cầu
tóm tắt trực tiếp và không dùng format, lượt 4 thành công.
Đây là cách phục hồi trong phiên demo, chưa phải bản sửa lỗi trong code.

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | Chưa có | Chưa thực hiện | UI không bật tool send; chưa cấu hình Telegram |
| arXiv/company policy | Chưa có bằng chứng demo | Chưa thực hiện demo các tool này | Không tính là chức năng đã kiểm chứng |
| UI | app.py | Giao diện Streamlit chạy local; hỗ trợ chat, xem tool results và lưu transcript | Chỉ bật clarify, lookup, fetch, format và deduplicate; chưa có link public |
| Tool unit tests | tests/test_deduplicate.py | 8 test cho tool mới đều đạt; toàn bộ suite đạt 75 passed, 17 skipped | Test chạy offline; 17 test TODO của starter chưa hoàn thành |
| Tool mới deduplicate | tools/deduplicate/tool.py; tools/deduplicate/TOOL.md | Loại URL trùng, giữ item đầu tiên và thứ tự; group eval G01/G09 và live demo đều thành công | Chỉ so sánh URL sau khi bỏ khoảng trắng hai đầu, không phát hiện nội dung giống nhau ở URL khác nhau |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.
Nhóm bổ sung 4 hàm test cho deduplicate, tạo thành 8 trường hợp
kiểm thử nhờ parametrization:

- Loại URL trùng, giữ bản đầu tiên và thứ tự, không sửa input.
- Giữ các item có URL thiếu, null, rỗng hoặc chỉ có khoảng trắng.
- Danh sách rỗng trả kết quả rỗng.
- Năm trường hợp input sai trả error dict thay vì raise exception.

Chưa ghi nhận bug đã xác minh trong các tool có sẵn.

Ví dụ hành vi unit test kiểm tra nhưng eval nhóm hiện chưa kiểm tra:
khi items=[{"url": 123}], tool phải trả error="invalid_input"
thay vì phát sinh exception. Hai case eval G01/G09 chỉ kiểm tra
model chọn đúng tool, không kiểm tra nhánh input sai này.

Lệnh kiểm tra:
python -m pytest tests/test_deduplicate.py -q
python -m pytest -q


## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
Các quy tắc chung về thiếu thông tin, chờ người dùng, xác nhận hành động và duy trì ngữ cảnh thuộc prompt. v1 sửa R10/R11; v4 sửa G07. Quy tắc xác nhận ở v3 chưa đủ để đạt R12, cho thấy cần đọc log thay vì suy ra rằng viết rule là model sẽ tuân thủ.
- Which fixes belonged in `tools.yaml`?
Mô tả tool cần nói rõ khi nào dùng/không dùng; mô tả tham số cần giải thích convention. v2 chỉnh query của lookup để tránh lặp topic/timeframe trong query; sửa được M02 nhưng R03 vẫn sai. Tool deduplicate cần khai báo items khớp signature và đăng ký registry; contract test kiểm tra sự đồng bộ này.
- Which failure needed manual review instead of automatic grading?
Query “AI news today” hợp lý về tìm kiếm nhưng không khớp chuỗi “AI” của bộ chấm, nên cần phân biệt sai convention với sai ý nghĩa. R12 hỏi nội dung còn thiếu là một hành vi thận trọng nhưng không khớp thứ tự yes_no của eval. Các case no_tool có thể PASS dù lời đáp không từ chối theo behavior kỳ vọng: ví dụ R08/R14 v0 trả lời toán/code; vì vậy không dùng điểm routing để khẳng định tuân thủ phạm vi. R09 v0 còn mô tả khả năng đăng tweet chưa được cung cấp. Chất lượng tóm tắt, độ đúng nguồn và lỗi tool/API đều cần kiểm tra ngoài điểm tự động.
- What would you improve next?
1. v5 đã bỏ câu ép một bước/một tool và bổ sung routing cho đủ 11 tool. Descriptions, handle, thời gian, loại tin và ranh giới gửi đã được làm rõ. Chưa chạy base/group bằng model thật với cấu hình v5, nên chưa khẳng định các lỗi base đã hết.
2. v5 đã bổ sung runtime riêng cho UI: giữ kết quả trung gian khi provider lỗi; chặn gửi trực tiếp từ model, cho duyệt đúng bản nháp/kênh bằng nút và không tự gửi lại. Chưa thay vòng chạy CLI chat.py, nên giới hạn logging của transcript demo cũ vẫn còn trong CLI.
3. Hoàn thiện 17 test TODO. Các test mới xác minh tích hợp nhưng không thay thế các bài TODO của starter.
4. Tạo link public và thử từ máy khác. UI lưu transcript cục bộ, chưa có xác thực/giới hạn sử dụng; chưa đánh giá cho triển khai rộng.
5. Bổ sung RapidAPI/Telegram nếu muốn dùng các tool cần key. papers đã thử kết nối thật nhưng timeout; paper_text đã tải/trích text thật thành công. Chưa có kết quả so sánh cloud/local.

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
