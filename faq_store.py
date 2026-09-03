"""
Lightweight FAQ store for the Almosafer voice agent.

Loads category-scoped Q&A JSON files (produced from the official Almosafer
FAQ pages) and does simple keyword-overlap retrieval - no embeddings/vector
DB needed at this dataset size (a few dozen Q&A per category).

Upgrade path (when the FAQ set grows or phrasing variance increases):
swap `_score()` for an embedding-similarity search (e.g. a small sentence
embedding model or an embeddings API) behind the same `search()` interface.
"""

import json
import re
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "faq_data"

# Arabic stopwords worth ignoring for scoring so they don't dominate overlap
_STOPWORDS = {
    "في", "من", "إلى", "على", "أن", "هل", "ما", "هو", "هي", "أو", "و",
    "التي", "الذي", "لا", "نعم", "عن", "مع", "قبل", "بعد", "كل", "أي",
    "يمكن", "يمكنني", "بإمكاني", "الخاص", "الخاصة", "عبر", "عند", "قد",
}

_WORD_RE = re.compile(r"[\w\u0600-\u06FF]+")

# Matches markdown links like [نص](https://...) -> keeps just "نص"
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# Matches bare URLs that slipped in without markdown wrapping
_BARE_URL_RE = re.compile(r"https?://\S+")


def _clean_for_speech(text: str) -> str:
    """Strip markdown links and bare URLs so TTS never reads them aloud."""
    text = _MD_LINK_RE.sub(r"\1", text)      # keep the link text, drop the URL
    text = _BARE_URL_RE.sub("", text)         # remove any remaining bare URLs
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def _tokenize(text: str) -> set:
    words = _WORD_RE.findall(text)
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


class FaqStore:
    def __init__(self):
        self._data: dict[str, list[dict]] = {}
        self._labels: dict[str, str] = {}

    def load(self, category_key: str, label: str, filename: str):
        path = DATA_DIR / filename
        entries = json.loads(path.read_text(encoding="utf-8"))
        for e in entries:
            e["question"] = _clean_for_speech(e["question"])
            e["answer"] = _clean_for_speech(e["answer"])
            e["_tokens"] = _tokenize(e["question"] + " " + e["answer"])
        self._data[category_key] = entries
        self._labels[category_key] = label

    def label(self, category_key: str) -> Optional[str]:
        return self._labels.get(category_key)

    def search(self, category_key: str, query: str, top_n: int = 2) -> list[dict]:
        entries = self._data.get(category_key, [])
        if not entries:
            return []
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        scored = []
        for e in entries:
            overlap = q_tokens & e["_tokens"]
            if overlap:
                score = len(overlap) / max(len(q_tokens), 1)
                scored.append((score, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_n] if _ > 0.15]


# Singleton used by agent.py
store = FaqStore()


def load_all():
    store.load("1", "الطيران", "flights.json")
    store.load("2", "الفنادق", "hotels.json")
    store.load("3", "شاليهات+", "chalets.json")
    store.load("4", "المدفوعات والرسوم", "payments.json")