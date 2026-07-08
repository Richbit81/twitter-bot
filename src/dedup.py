from __future__ import annotations

import re
import string


def normalize_text(text: str) -> str:
    lowered = text.lower()
    cleaned = lowered.translate(str.maketrans("", "", string.punctuation))
    return " ".join(cleaned.split())


def word_set(text: str) -> set[str]:
    normalized = normalize_text(text)
    words = normalized.split()
    return {w for w in words if len(w) > 2}


def jaccard_similarity(a: str, b: str) -> float:
    set_a = word_set(a)
    set_b = word_set(b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def is_duplicate(
    tweet: str,
    history_entries: list[dict],
    threshold: float,
    limit: int = 50,
) -> bool:
    recent = history_entries[-limit:]
    normalized_new = normalize_text(tweet)

    for entry in recent:
        previous = entry.get("text", "")
        if normalize_text(previous) == normalized_new:
            return True
        if jaccard_similarity(tweet, previous) >= threshold:
            return True

    return False


def ensure_url_present(tweet: str, url: str) -> bool:
    return url in tweet or url.replace("https://", "") in tweet


def validate_tweet(tweet: str, max_chars: int, url: str) -> tuple[bool, str]:
    text = tweet.strip()
    if not text:
        return False, "Tweet is empty"
    if len(text) > max_chars:
        return False, f"Tweet exceeds {max_chars} characters ({len(text)})"
    if not ensure_url_present(text, url):
        return False, f"Tweet must include URL: {url}"
    if re.search(r"\b(buy now|don't miss|limited time|to the moon)\b", text, re.I):
        return False, "Tweet contains banned hype phrases"
    return True, ""
