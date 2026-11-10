# Research Agent — bản tích hợp đủ tool

## Chạy sản phẩm

Mở PowerShell tại `starter_v0`, dùng Python của môi trường đã có:

```powershell
..\.venv\Scripts\python.exe -m streamlit run app.py
```

Nếu Streamlit đang chạy bản cũ, Ctrl+C rồi chạy lại. Giao diện mở tại địa chỉ local mà Streamlit hiển thị, thường là http://localhost:8501.

Bản `v5-all-tools` bắt đầu phiên mới để không trộn lịch sử/tool declarations của UI cũ. Các transcript đã ghi trên đĩa được giữ nguyên.

## Danh sách đầy đủ

| Tool | Dùng khi | Cần cấu hình |
|---|---|---|
| clarify | Thiếu URL, tài khoản, cần hỏi/xác nhận | Không |
| timeline | Bài đăng của một tài khoản X/Twitter | RAPIDAPI_KEY và đăng ký Twitter API45 |
| social_search | Bài đăng về một chủ đề trên X/Twitter | Cùng key và đăng ký như timeline |
| lookup | Tìm trên web, tin tức theo thời gian | TAVILY_API_KEY |
| fetch | Đọc một URL cụ thể | FIRECRAWL_API_KEY |
| format | Định dạng dữ liệu đã có thành bản tin | Không |
| send | Tạo bản nháp Telegram, duyệt và gửi | TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID |
| policy | Tra cứu chính sách nội bộ | Thư mục company_policy có tài liệu |
| papers | Tìm paper trên arXiv | Internet; không cần API key |
| paper_text | Tải/trích text paper arXiv đã có ID | Internet, pypdf; lưu PDF/text trong arxiv_papers |
| deduplicate | Loại URL trùng trong danh sách đã có | Không; tool do nhóm thêm |

Tất cả 11 tool được khai báo cho model trong UI. Tool thiếu key vẫn xuất hiện trong danh sách nhưng runtime trả lỗi cấu hình trước khi gọi mạng. Dấu đã cấu hình không có nghĩa API đã được kiểm chứng sống.

## File .env

Giữ cấu hình Groq đang hoạt động:

```dotenv
OPENROUTER_API_KEY=<key Groq của bạn>
OPENROUTER_BASE_URL=https://api.groq.com/openai/v1
TAVILY_API_KEY=<key Tavily>
FIRECRAWL_API_KEY=<key Firecrawl>
RAPIDAPI_KEY=<key RapidAPI, khi đã đăng ký API45>
RAPIDAPI_TWITTER_HOST=twitter-api45.p.rapidapi.com
TELEGRAM_BOT_TOKEN=<token bot Telegram>
TELEGRAM_CHAT_ID=<ID kênh hoặc @channel>
ARXIV_USER_AGENT=Randoms-Research-Agent/1.0
```

Chỉ điền key đã có, không dán các giá trị mẫu trong dấu <>. Tool chưa dùng có thể để key trống. Không đưa .env hoặc key vào report/chat. Sau khi lưu .env, bấm **Tải lại cấu hình**.

Telegram: bot cần được thêm vào kênh với quyền đăng bài. Model chỉ tạo bản nháp, kể cả khi nó truyền confirmed=true. Giao diện hiển thị đúng nội dung/kênh và chờ nút **Xác nhận gửi bản nháp này**. Có thể hủy mà không gửi. Đổi kênh làm xác nhận cũ không còn hợp lệ. Mỗi bản nháp chỉ được thực hiện một lần; khi gặp lỗi, kiểm tra kênh trước khi chủ động tạo bản gửi mới.

## Demo các tool mới bật

1. `Lấy 3 tweet mới nhất của @karpathy.`
2. `Tìm các tweet phổ biến nhất về AI.`
3. `Chính sách nội bộ quy định thế nào về trích dẫn nguồn?`
4. `Tìm 2 paper arXiv về retrieval augmented generation.`
5. `Đọc paper arXiv 1706.03762, tối đa 2 trang, tóm tắt và dẫn nguồn.`
6. Sau khi có bản tin: `Tạo bản nháp gửi bản tin vừa có lên Telegram, chờ tôi duyệt.`

Các lượt model dùng token Groq; công cụ mạng dùng hạn mức dịch vụ tương ứng. Không gọi model chỉ bằng việc mở UI hoặc xem danh sách công cụ.

## Kiểm tra và bằng chứng

```powershell
python -m pytest -q
```

`tests/test_product_runtime.py` kiểm tra dispatch đủ tool, cấu hình thiếu, dừng clarify, giữ bằng chứng khi provider lỗi và ranh giới Telegram. `tests/test_product_ui.py` dùng Streamlit AppTest kiểm tra UI, lưu transcript và hủy gửi, không gọi model/mạng thật.

Transcript v5 lưu prompt, tool declarations và hash của prompt/tools/runtime/app. Lỗi provider giữa vòng không làm mất các tool results đã thu được. Không có tự động retry gửi Telegram. Không coi kiểm thử mock là bằng chứng API Twitter/Telegram/arXiv đã hoạt động thật.

Các log v0–v4 vẫn là bằng chứng của những phiên bản trước. Sau khi thay prompt và mô tả tool ở v5, cần eval mới nếu muốn công bố điểm của v5; không gán điểm 85%/100% cũ cho phiên bản mới.
