# Kế hoạch nhóm — Lab Day 03 Research Agent Tool Eval

**Mục tiêu:** làm đủ phần bắt buộc **và** lấy điểm thưởng (UI Streamlit + 4 tool mới). Provider: **OpenRouter** (`openai/gpt-4o-mini`). Không làm bài Small Local Model.

Đọc mục **1. Vai**, tìm vai của mình, rồi xem **3. Lịch** để biết mỗi mốc giờ phải giao gì.

**Hiện tại tự hoàn thành hết, sau đó đối chiếu với các thành viên khác để chọn bài mới nhất**

---

## 1. Vai

| Vai                       | Người | File chỉ mình được sửa                                                            | Việc                                                                                                                                                                                  |
| ------------------------- | ------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Chủ lời nhắc        | Cường | `artifacts/system_prompt.md`, `artifacts/tools.yaml`, `artifacts/version_log.csv` | Chạy v0 → v3, mỗi vòng **một** giả thuyết, ghi log ngay sau mỗi lần chạy. Gộp khai báo tool mới vào `tools.yaml`.                                                |
| 2. Người đọc log      | Cường | `analysis/*.csv`                                                                      | Đọc `runs/*.json`, gán loại lỗi cho từng case FAIL, đề xuất giả thuyết cho vòng sau. Lúc chờ chạy eval: viết các test challenge trong `tests/test_tools_todo.py`. |
| 3. Thợ công cụ         | Cường | `tools/<tool mới>/`, `tools/__init__.py`, test của tool mới                      | Viết 4 tool mới + `TOOL.md` + ≥ 3 test mỗi tool. Giữ `pytest` xanh. Gửi đoạn YAML khai báo cho vai 1.                                                                     |
| 4. Người ra đề        | Cường | `data/eval_group.json`                                                                | Viết 10 case (5 một lượt, 5 nhiều lượt) dựa trên lỗi thật trong log v0 và trên 4 tool mới. Chạy bộ eval nhóm.                                                         |
| 5. Giao diện + báo cáo | Cường | `app.py`, `transcripts/`, `artifacts/REPORT.md`, `artifacts/poster.html`        | Dựng UI Streamlit, mở Cloudflare Tunnel, chat thử 3 lượt, viết REPORT Phần A **trước 16:30**, tổng hợp Phần B.                                                       |

2. Quy tắc chung

1. **Chỉ vai 1 sửa `system_prompt.md` và `tools.yaml`.** Muốn đổi gì thì nhắn vai 1. Lý do: mỗi version chỉ được một giả thuyết; hai người cùng sửa thì không biết điểm lên/xuống vì đâu.
2. **Không ai sửa gì trước khi v0 chạy xong.** v0 là "điểm trước" cho mọi so sánh.
3. **Mỗi người một nhánh git** `feature/<tên>-<vai>`; một người gộp vào `main`. Chạy `pytest` trước mỗi lần gộp.
4. **Thứ tự gộp:** khai báo tool mới trong `tools.yaml` phải vào `main` **trước** các case eval gọi tool đó. Nếu ngược lại, `tests/test_tool_contract.py` sẽ đỏ.
5. **Mỗi người tự giữ `.env`.** Không dán key vào chat nhóm, báo cáo, ảnh chụp hay GitHub.
6. **Họp đứng 5 phút** ở mỗi mốc 15:00 / 15:30 / 16:00 / 16:30 / 17:30.
7. **Không đổi tên tool đã chốt** (mục 4). Nếu buộc phải đổi: báo cả nhóm và đổi đủ ở `tools.yaml`, `tools/__init__.py`, các file `data/eval_*.json`.

## 3. Lịch theo mốc

| Mốc                    | Phải có                                                                                                                                         |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Trước 15:00** | Mỗi người: cài xong (mục 6), preflight pass, `pytest` xanh. Cả nhóm chốt bảng tool mới (mục 4).                                      |
| **15:00**         | Vai 1 chạy v0 và ghi log. Vai 2 đọc log v0. Vai 3 bắt đầu tool `wiki` + test. Vai 5 dựng `app.py`.                                    |
| **15:30**         | Vai 1 có v1. Vai 3 có ≥ 1 tool mới, test xanh, gửi YAML cho vai 1. Vai 4 bắt đầu viết case từ lỗi v0. UI chạy được ở máy local.  |
| **16:00**         | Vai 1 có v2 (đã khai báo 4 tool mới), chạy bộ base + bộ nhóm. Vai 4 xong 10 case. Vai 5 mở tunnel, viết Phần A.                       |
| **16:30**         | **Team showdown.** Link dùng thử chạy được; REPORT Phần A / poster xong.                                                             |
| **17:30**         | Vai 1 có v3, log đủ v0–v3. Test challenge: 0 skipped. Chat thử ≥ 3 lượt có transcript. Phần B viết từ log thật. **Nộp bài.** |

## 4. Bảng tool mới (đã chốt — dùng chung cho vai 1, 3, 4)

Cả 4 tool đều không cần API key.

| Tên tool         | Tham số                                                                          | API                                                     | Dùng khi nào (khác `lookup` ở đâu)                                                           |
| ----------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `wiki`          | `title`, `lang` (`vi`/`en`, mặc định `en`)                           | Wikipedia REST `/api/rest_v1/page/summary/{title}`    | Định nghĩa, kiến thức nền về khái niệm, người, tổ chức. Không dùng cho tin thời sự. |
| `hn_search`     | `query`, `sort` (`relevance`/`date`), `limit`                           | `hn.algolia.com/api/v1/search` và `search_by_date` | User nhắc rõ Hacker News.                                                                          |
| `github_search` | `query`, `language`, `sort` (`stars`/`updated`), `limit`              | `api.github.com/search/repositories`                  | Tìm repo, thư viện, mã nguồn.                                                                   |
| `hf_models`     | `query`, `task` (pipeline_tag), `sort` (`downloads`/`likes`), `limit` | `huggingface.co/api/models`                           | Tìm model trên Hugging Face.                                                                       |

## 5. Ghi chú theo vai

### Vai 1 — kế hoạch các vòng

| Version | File sửa            | Giả thuyết                                                                                                                                                                                                                                                                                                                                                          | Case kỳ vọng sửa được                                          |
| ------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| v0      | —                   | Baseline, không sửa gì                                                                                                                                                                                                                                                                                                                                             | —                                                                   |
| v1      | `system_prompt.md` | Bỏ 3 chỉ dẫn xấu cố ý (đoán thay vì hỏi, gửi không cần xác nhận, ép một tool). Thêm rule: thiếu tài khoản/URL thì `clarify` với `response_type=text`; yêu cầu gửi/đăng thì `clarify` với `response_type=yes_no` trước; được gọi nhiều tool khi cần nhiều nguồn; câu meta/toán/code thì trả lời không gọi tool. | R08–R14, M01, M04                                                   |
| v2      | `tools.yaml`       | Mỗi tool ghi rõ _khi nào dùng / khi nào không dùng_ và quy ước tham số; khai báo luôn 4 tool mới theo cùng chuẩn.                                                                                                                                                                                                                                   | R01, R03, R05–R07, M02, M06; điểm base không tụt dù thêm tool |
| v3      | `system_prompt.md` | Rule nhiều lượt: lượt mới nhất quyết định, giữ lại tham số từ lượt trước, lượt sau sửa thì ghi đè. Thêm các sửa theo đề xuất của vai 2.                                                                                                                                                                                                | M03, M05 + case còn sót                                            |

Ghi `version_log.csv` **ngay sau mỗi lần chạy, kể cả khi điểm tụt**. `prompt_hash`, `tools_hash`, `run_file` lấy từ output của `run_eval.py`.

### Bẫy chấm điểm cần biết (vai 1, 2, 4)

- Tham số được so **khớp chính xác** (chỉ bỏ hoa/thường và khoảng trắng). Ví dụ `lookup` phải có `query="AI"`, không được là `"AI news today"`. Quy ước: `query` chỉ là từ khóa chủ đề; "hôm nay/tuần này" đưa vào `timeframe`; "tin tức" thì `topic=news`.
- **Gọi thừa tool cũng là FAIL.** Ví dụ R03 mà gọi thêm `social_search` là trượt.
- `clarify` bị chấm cả `response_type`: `text` khi thiếu thông tin, `yes_no` khi cần xác nhận gửi.
- Tên người phải đổi thành handle không có `@`: Sam Altman → `sama`, Elon Musk → `elonmusk`, Andrej Karpathy → `karpathy`.
- Case nhiều lượt được gộp thành một tin nhắn "Earlier turns… / Latest user turn…".
- Chạy eval **gọi tool thật**, nên tốn credit Tavily/Firecrawl/RapidAPI. Đừng chạy thử bừa. Nếu `.env` có Telegram và model gọi `send(confirmed=true)` thì tin nhắn được gửi thật.

### Vai 3 — chuẩn viết tool

- Làm theo mẫu `tools/lookup/tool.py`: dùng `requests.get`, dùng `TIMEOUT`, `err`, `domain` từ `tools/_shared.py`.
- Trả về `{"tool": ..., "items": [{"title", "url", "source", "summary"}]}` để tool `format` dùng lại được.
- Kiểm tra input: chuỗi rỗng thì trả error dict; ép `limit` về `int`; giá trị ngoài enum thì về mặc định. **Không bao giờ raise.**
- `TOOL.md` có frontmatter đúng như `tools/README.md`. Đăng ký tool trong `TOOL_FUNCTIONS` ở `tools/__init__.py`.
- Mỗi tool ≥ 3 test: (1) chạy đúng, mock HTTP bằng `fake_http` và assert cả request gửi đi; (2) input xấu từ model; (3) lỗi HTTP 429/timeout trả error dict. Mẫu xem `tests/test_tools_examples.py`.

### Vai 2 — test challenge

Điền hết các stub `pytest.skip(TODO)` trong `tests/test_tools_todo.py` (clarify, format, send, lookup, fetch, timeline, social_search, policy). Thử thêm input biên như `limit=0`, `top_k=0`, `max_results="5"`, `items` thiếu `url`. Nếu thấy bug thì sửa, giữ lại test đã bắt được bug, và ghi vào REPORT mục B5.

### Vai 4 — eval nhóm

- Mỗi case cần: `id`, `phase: "B"`, `query` hoặc `turns`, `failure_type` (một trong `wrong_tool`, `wrong_arg_value`, `wrong_boundary`, `unnecessary_tool`, `out_of_scope`, `missing_info`), `expect`, `metadata.what_it_tests`.
- Khung gợi ý (sửa theo log v0):
  - **Một lượt:** 4 case gọi 4 tool mới, cộng 1 case lấy từ lỗi thật của v0.
  - **Nhiều lượt:** xác nhận rồi mới gửi (`send` với `confirmed=true`); đổi từ tìm web sang Hacker News nhưng giữ chủ đề; sửa ngôn ngữ khi tìm repo GitHub; hỏi lại rồi bổ sung → `wiki`; giữ `search_type=Top` và sửa `limit`.
- Trong `expect.args` chỉ ghi những tham số chắc chắn đúng, vì tham số được chấm khớp chính xác.

### Vai 5 — UI

- `app.py` dùng lại `run_model_tool_loop`, `write_transcript`, `trim_history` từ `chat.py`. Không viết lại vòng lặp agent.
- Sidebar: chọn provider/model, nhãn version, nút "Cuộc hội thoại mới". Mỗi lượt có ô mở rộng hiện tool calls, args và kết quả. Mỗi lượt đều lưu transcript vào `transcripts/`.
- Thêm `streamlit` vào `requirements.txt`.
- Chạy và mở link: `streamlit run app.py`, sau đó `cloudflared tunnel --url http://localhost:8501`. Dán URL vào REPORT mục A1 và giữ lệnh chạy suốt buổi showdown.
- Trên bản public không hiện key hay biến môi trường. Giữ cơ chế xác nhận trước khi `send`.
- Chat thử ≥ 3 lượt: một yêu cầu research bình thường; một yêu cầu thiếu thông tin rồi bổ sung ở lượt sau; một yêu cầu đăng lên Telegram (agent phải hỏi xác nhận trước).

## 6. Cài đặt (mỗi người, trước 15:00)

```powershell
cd starter_v0
python -m venv .venv          # nếu lỗi khi cài streamlit trên Python 3.14: py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # điền OPENROUTER_API_KEY, TAVILY_API_KEY, FIRECRAWL_API_KEY, RAPIDAPI_KEY
python scripts/preflight_provider.py --provider openrouter
pytest
```

Cách lấy key: xem `TOOL-SETUP.md`.

## 7. Lệnh hay dùng

```powershell
# Bộ eval base (vai 1) — đổi v0 thành v1/v2/v3
python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json

# Bộ eval nhóm (vai 4)
python run_eval.py --provider openrouter --version v2 --suite group --eval-cases data/eval_group.json

# Chuyển log thành CSV (vai 2)
python scripts/parse_runs.py runs/ --output analysis/base_runs.csv

# Chat trên terminal (vai 5)
python chat.py --provider openrouter --version v3
```

## 8. Checklist trước khi nộp

- [ ] `version_log.csv` có đủ v0, v1, v2, v3
- [ ] Có đủ `runs/*.json` và `transcripts/`
- [ ] `eval_group.json` có 10 case, trong đó có case gọi tool mới
- [ ] `pytest`: 0 failed, 0 skipped; mỗi tool mới có ≥ 3 test
- [ ] REPORT có Phần A và Phần B
- [ ] Không có `.env`, không có key trong code hay báo cáo
