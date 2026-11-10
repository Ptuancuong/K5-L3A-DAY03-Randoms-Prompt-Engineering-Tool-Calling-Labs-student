---
name: sentiment_analyzer
description: "Phân tích sắc thái cảm xúc (Sentiment Analysis) của đoạn văn bản hoặc bài đăng (positive, negative, neutral) và trích xuất điểm phân cực cùng các từ khóa nổi bật."
parameters:
  type: object
  properties:
    text:
      type: string
      description: "Đoạn văn bản, bài đăng tweet hoặc tóm tắt cần phân tích sắc thái cảm xúc."
  required:
    - text
---

# sentiment_analyzer

Tool phân tích sắc thái văn bản (NLP sentiment analysis):
- Trả về nhãn: `positive`, `negative`, `neutral`
- Tính toán điểm phân cực (`polarity_score` từ -1.0 đến +1.0)
- Trích xuất danh sách các từ khóa cảm xúc và giải thích ngắn gọn.
