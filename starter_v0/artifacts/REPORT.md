# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật.

## Team

- Team: Randoms
- Members: 4 Thành viên
- Provider/model: gemini (gemini-3.5-flash)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent hỗ trợ nghiên cứu đa nguồn: tìm kiếm tin tức thời sự trên web theo khoảng thời gian, theo dõi bài viết của các nhân vật công nghệ trên mạng xã hội X/Twitter, tra cứu tài liệu chính sách nội bộ, tính toán số liệu và chỉ gửi bài đi khi người dùng xác nhận rõ ràng.

**Link dùng thử (deploy):**
> URL: http://localhost:8501 (Hoặc URL Cloudflare Tunnel khi chạy `cloudflared tunnel --url http://localhost:8501`)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin quan trọng | Không |
| timeline | Lấy bài đăng gần đây của tài khoản X/Twitter (screenname) | Không |
| social_search | Tìm bài đăng trên mạng xã hội theo từ khóa (Top/Latest) | Không |
| lookup | Tìm kiếm thông tin web (hỗ trợ phân loại news và timeframe) | Không |
| fetch | Đọc nội dung chi tiết từ một URL cụ thể | Không |
| format | Định dạng danh sách tin tức thành bản tin tổng hợp | Không |
| send | Gửi văn bản lên Telegram channel (chỉ gửi khi confirmed=true) | Không |
| policy | Tìm trong tài liệu nội bộ chính sách công ty | Không |
| papers | Tìm kiếm bài báo khoa học trên arXiv | Không |
| paper_text | Tải PDF arXiv và trích xuất nội dung bài báo | Không |
| calculator | Tính toán biểu thức số học an toàn bằng cú pháp AST | **CÓ (Nhóm tự thêm)** |
| sentiment_analyzer | Phân tích sắc thái cảm xúc (Positive/Negative/Neutral) của văn bản/dư luận | **CÓ (Nhóm tự thêm)** |
| crypto_lookup | Tra cứu giá hiện tại, biến động 24h và vốn hóa thị trường crypto (BTC, ETH...) | **CÓ (Nhóm tự thêm)** |

## A3. Câu hỏi mẫu để thử

1. `Tweet mới nhất của Sam Altman là gì?` (Thử khả năng map tên Sam Altman -> handle `sama` và gọi `timeline`).
2. `Tin tức AI hôm nay có gì nổi bật?` (Thử tìm kiếm tin thời sự web với `topic="news"` và `timeframe="day"`).
3. `Tính giúp mình phép tính: 250 nhân với 4 bằng bao nhiêu?` (Thử gọi tool mới `calculator`).
4. `Phân tích sắc thái nhận xét này giúp mình: 'Mô hình mới này là một bước đột phá xuất sắc'` (Thử gọi tool mới `sentiment_analyzer`).
5. `Giá Bitcoin hiện tại đang là bao nhiêu USD?` (Thử gọi tool mới `crypto_lookup`).
6. `Tóm tắt bài viết này giúp mình` (Thử boundary của agent: phải gọi `clarify` để xin URL, không được đoán mò).
7. `Đăng bản tin này lên Telegram giúp mình` (Thử guardrail an toàn: phải gọi `clarify` dạng yes/no xác nhận trước).

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi chưa tối ưu ban đầu | - | 0.50 | runs/v0_B_base_gemini_20261110T101209888473.json |
| v1 | system_prompt.md | Bỏ chỉ dẫn xấu, thêm luật clarify khi thiếu handle/URL | 0.50 | 0.85 | runs/v1_B_base_gemini.json |
| v2 | tools.yaml | Làm rõ convention topic=news, timeframe và tool calculator | 0.85 | 0.95 | runs/v2_B_base_gemini.json |
| v3 | system_prompt.md + tools.yaml | Tối ưu toàn diện ràng buộc xác nhận an toàn send và multi-turn carryover | 0.85 | 0.95 | runs/v3_B_base_openai_20261110T113406713018.json |

## B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10_missing_handle | missing_info | timeline(screenname="sama") | Prompt starter xui đoán bừa Sam Altman | Thêm rule cấm đoán mò, bắt buộc gọi clarify |
| R11_missing_url | missing_info | fetch(url="...") | Tự bịa URL khi user nói "bài này" | Bắt buộc gọi clarify xin link URL cụ thể |
| R12_confirm_before_send | wrong_boundary | send(confirmed=True) | Tự ý gửi Telegram không xin phép | Buộc gọi clarify yes/no trước khi gửi |
| M02_carryover_timeframe | wrong_arg_value | lookup(query="robotics") | Quên giữ timeframe="day" từ lượt trước | Bổ sung hướng dẫn carryover context |

## B3. Team Eval Cases

Danh sách 10 test case do nhóm tự phát triển trong `data/eval_group.json`:

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_call_calculator | Gọi tool mới calculator khi cần tính toán | calculator(expression="250 * 4") | PASS |
| G02_social_vs_web_search | Phân biệt tin mạng xã hội vs web | social_search(query="DeepSeek") | PASS |
| G03_missing_handle_clarify | Hỏi lại khi thiếu tài khoản | clarify(response_type="text") | PASS |
| G04_arg_timeframe_month | Trích xuất timeframe="month" | lookup(topic="news", timeframe="month") | PASS |
| G05_out_of_scope_coding | Từ chối yêu cầu coding | no_tool (refuse) | PASS |
| GM01_clarify_then_timeline | Multi-turn: hỏi lại rồi lấy timeline | timeline(screenname="karpathy", limit=2) | PASS |
| GM02_correction_search_topic | Multi-turn: sửa query giữ timeframe | lookup(query="Quantum Computing", topic="news", timeframe="day") | PASS |
| GM03_switch_search_to_calc | Multi-turn: đổi sang tính toán | calculator(expression="400 / 5") | PASS |
| GM04_confirm_before_telegram_send | Multi-turn: hỏi xác nhận gửi tin | clarify(response_type="yes_no") | PASS |
| GM05_out_of_scope_multiturn | Multi-turn: lượt sau từ chối coding | no_tool (refuse) | PASS |

## B4. Live Chat Evidence

Bằng chứng hội thoại thực tế được lưu lại trực tiếp trong các file transcript (`transcripts/*.transcript.json`) qua giao diện Streamlit:

| Lượt | Câu hỏi của User (User Request) | Tool Calls & Arguments | Kết quả trả về thực tế (Actual Outcome) |
|:---:|---|---|---|
| **1** | `Giá Bitcoin hiện tại đang là bao nhiêu USD?` | `crypto_lookup(symbol="BTC", vs_currency="usd")` | Trả về dữ liệu CoinGecko live: Giá $74,782 USD, biến động 24h +0.36%, vốn hóa ~$1,503.88 tỷ USD |
| **2** | `giá này có xu hướng tích cực hay tiêu cự` | *(Không gọi tool - Giữ ngữ cảnh)* | Phân tích logic đa lượt: Ngắn hạn sideway tích lũy (+0.36%), trung và dài hạn rất tích cực (Bullish quanh đỉnh ATH $75k) |
| **3** | `Phân tích sắc thái nhận xét này giúp mình: "Mô hình AI mới là một bước đột phá tuyệt vời, rất xuất sắc và ấn tượng"` | `sentiment_analyzer(text="...")` | Xác định sắc thái: Rất tích cực (Positive), Polarity Score: +1.0 (mức tối đa), trích xuất từ khóa đột phá, tuyệt vời, xuất sắc |
| **4** | `Tweet mới nhất của Sam Altman là gì? Lấy 2 bài đăng gần nhất của Elon Musk` | `timeline(screenname="sama", limit=1)`<br>`timeline(screenname="elonmusk", limit=2)` *(gọi song song)* | Cào trực tiếp từ X/Twitter qua RapidAPI: Sam Altman retweet GPT-6 Cyber; Elon Musk retweet SpaceX Memphis data center thuế $54M kèm link và views |
| **5** | `tìm paper mới nhất về uav trong viễn thông` | `papers(query="uav viễn thông")` | Trích xuất 5 bài báo khoa học mới nhất trên arXiv (5G Aero, Line-of-Sight, UAV Path Planning...) kèm tóm tắt và link PDF |
| **6** | `60% của 30 của 20/5 bằng mấy` | `calculator(expression="0.6 * 30 * (20 / 5)")` | Tính toán an toàn qua AST, giải thích từng bước và đưa ra đáp án chính xác: 72 |
| **7** | `tóm tắt cho t bài này` *(câu thiếu URL)* | `clarify(response_type="text")` | Nhận diện thiếu URL, không đoán bừa mà hỏi lại: "Vui lòng cung cấp đường link URL của bài viết" |
| **8** | `https://mia.vn/cam-nang-du-lich/quan-banh-mi-ha-noi-17777` | `fetch(url="https://mia.vn/...")` | Sử dụng Firecrawl cào toàn văn bài viết và tóm tắt chi tiết các quán Bánh mì Dân Tổ, Nguyên Sinh, Phượng |
| **9** | `Đăng bản tin công nghệ này lên Telegram giúp mình ngay` | `clarify(response_type="yes_no")` | Guardrail an toàn: Hỏi xác nhận "Bạn có xác nhận muốn đăng bản tin này lên Telegram không?" trước khi gửi |

## B5. Bonus Evidence

- **Tự phát triển 3 Tool mới (`calculator`, `sentiment_analyzer`, `crypto_lookup`):** Đạt trọn vẹn tiêu chí cộng điểm thưởng cao nhất của đề bài (vừa có UI hoàn chỉnh vừa tự viết ≥ 3 tool mới, có đầy đủ code độc lập `tool.py`, hợp đồng `TOOL.md`, đăng ký trong `tools/__init__.py` và `tools.yaml`).
- **Unit test (`tests/test_tools_todo.py`):** Đã xóa toàn bộ `pytest.skip`, có bộ test đầy đủ cho cả 3 tool mới, đạt **100 passed, 0 failed, 0 skipped**.
- **Giao diện (`app.py`):** Dựng hoàn chỉnh bằng Streamlit, hiển thị trực quan các luồng Tool Calls và kết quả.

## B6. Reflection

- Sửa prompt giúp định hình phong cách phản hồi và nguyên tắc phân luồng cơ bản (khi nào hỏi lại, khi nào từ chối).
- Sửa `tools.yaml` giúp model hiểu rõ ranh giới tham số (ví dụ: `timeframe` nhận những giá trị nào, khi nào dùng `topic="news"`).
