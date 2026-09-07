"""Shared text normalization for the deterministic eval metrics.

gpt-oss (and other models) consistently write typographic Unicode
punctuation - curly quotes, non-breaking hyphens - where Gemini Flash more
often used plain ASCII. Every regex-based check in this package was written
and tuned against ASCII punctuation (e.g. `can(?:'|no)t help` requires a
straight apostrophe), so a model that writes "can't" with a curly apostrophe
(U+2019) silently fails every one of those checks - not because it behaved
incorrectly, but because the text never matched.

Normalizing once here, rather than patching every affected pattern
individually, fixes the whole category at once and prevents it recurring
as new patterns get added.
"""

_REPLACEMENTS = {
    "‘": "'", "’": "'",   # curly single quotes -> straight
    "“": '"', "”": '"',  # curly double quotes -> straight
    "‑": "-",                  # non-breaking hyphen -> ASCII hyphen
    "–": "-", "—": "-",  # en/em dash -> ASCII hyphen
    " ": " ", " ": " ",  # non-breaking / narrow no-break space -> space
}


def normalize(text: str) -> str:
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text
