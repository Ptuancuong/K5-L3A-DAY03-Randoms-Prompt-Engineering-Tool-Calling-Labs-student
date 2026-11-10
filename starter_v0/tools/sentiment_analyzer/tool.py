from __future__ import annotations

import re
from typing import Any

POSITIVE_WORDS = {
    # English
    "good", "great", "excellent", "amazing", "wonderful", "breakthrough", "promising",
    "bullish", "profit", "gain", "success", "successful", "innovative", "impressive",
    "love", "outstanding", "superior", "upgrade", "optimistic", "growth",
    # Vietnamese
    "tot", "tuyet", "hay", "xuat sac", "dot pha", "trien vong", "thanh cong",
    "tang truong", "ung ho", "tich cuc", "khen", "yeu thich", "hap dan"
}

NEGATIVE_WORDS = {
    # English
    "bad", "terrible", "awful", "horrible", "poor", "fail", "failure", "crash",
    "bearish", "loss", "danger", "dangerous", "risk", "risky", "bug", "scam",
    "drop", "plunge", "decline", "criticism", "hate", "pessimistic", "flaw",
    # Vietnamese
    "xau", "te", "kem", "that bai", "sup do", "nguy hiem", "rui ro", "loi",
    "giam", "chi trich", "tieu cuc", "that vong", "scam", "lua dao"
}

NEGATIONS = {"not", "no", "never", "hardly", "khong", "chua", "chang"}


def _normalize(text: str) -> str:
    # Remove accents for simple Vietnamese matching
    text = text.lower()
    replacements = {
        "à": "a", "á": "a", "ả": "a", "ã": "a", "ạ": "a",
        "ă": "a", "ằ": "a", "ắ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a",
        "â": "a", "ầ": "a", "ấ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a",
        "è": "e", "é": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
        "ê": "e", "ề": "e", "ế": "e", "ể": "e", "ễ": "e", "ệ": "e",
        "ì": "i", "í": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
        "ò": "o", "ó": "o", "ỏ": "o", "õ": "o", "ọ": "o",
        "ô": "o", "ồ": "o", "ố": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
        "ơ": "o", "ờ": "o", "ớ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
        "ù": "u", "ú": "u", "ủ": "u", "ũ": "u", "ụ": "u",
        "ư": "u", "ừ": "u", "ứ": "u", "ử": "u", "ữ": "u", "ự": "u",
        "ỳ": "y", "ý": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
        "đ": "d",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def analyze_sentiment(text: str) -> dict[str, Any]:
    """Phân tích sắc thái cảm xúc (Sentiment Analysis) của văn bản.
    
    Trả về nhãn (positive, negative, neutral), điểm phân cực (-1.0 đến +1.0) và từ khóa.
    """
    if not isinstance(text, str) or not text.strip():
        return {
            "tool": "sentiment_analyzer",
            "error": "ValueError",
            "message": "Nội dung văn bản (text) không được để trống.",
        }

    clean_text = _normalize(text)
    words = re.findall(r"\b\w+\b", clean_text)
    if not words:
        return {
            "tool": "sentiment_analyzer",
            "sentiment": "neutral",
            "polarity_score": 0.0,
            "confidence": 0.5,
            "positive_signals": [],
            "negative_signals": [],
            "summary": "Không phát hiện đủ tín hiệu ngôn ngữ rõ rệt.",
        }

    pos_hits: list[str] = []
    neg_hits: list[str] = []

    for i, word in enumerate(words):
        is_negated = i > 0 and words[i - 1] in NEGATIONS
        if word in POSITIVE_WORDS:
            if is_negated:
                neg_hits.append(f"{words[i-1]} {word}")
            else:
                pos_hits.append(word)
        elif word in NEGATIVE_WORDS:
            if is_negated:
                pos_hits.append(f"{words[i-1]} {word}")
            else:
                neg_hits.append(word)

    pos_count = len(pos_hits)
    neg_count = len(neg_hits)
    total_signals = pos_count + neg_count

    if total_signals == 0:
        polarity = 0.0
        sentiment = "neutral"
        confidence = 0.6
        summary = "Văn bản mang sắc thái trung lập hoặc khách quan."
    else:
        polarity = round((pos_count - neg_count) / total_signals, 2)
        if polarity > 0.15:
            sentiment = "positive"
            summary = f"Văn bản mang sắc thái tích cực (điểm phân cực: +{polarity})."
        elif polarity < -0.15:
            sentiment = "negative"
            summary = f"Văn bản mang sắc thái tiêu cực (điểm phân cực: {polarity})."
        else:
            sentiment = "neutral"
            summary = f"Văn bản có sắc thái cân bằng/trung lập (điểm phân cực: {polarity})."
        confidence = round(min(0.5 + 0.1 * total_signals, 0.95), 2)

    return {
        "tool": "sentiment_analyzer",
        "sentiment": sentiment,
        "polarity_score": polarity,
        "confidence": confidence,
        "positive_signals": pos_hits,
        "negative_signals": neg_hits,
        "summary": summary,
    }
