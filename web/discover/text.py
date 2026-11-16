import re
import unicodedata

_BRACKETS = re.compile(r"[(\[][^)\]]*[)\]]")
_FEAT = re.compile(r"\s+(feat\.?|ft\.?|featuring|with)\s+.*$")
_SUFFIX = re.compile(r"\s+-\s+.*$")
_NON_WORD = re.compile(r"[^\w]+")


def words(text: str) -> str:
    """Lowercase, accent-free words of the full text, brackets included."""
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return _NON_WORD.sub(" ", text).strip()


def normalize(text: str) -> str:
    """Lowercase, accent-free form of a title or artist without brackets, featured artists or ' - ' suffixes."""
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    text = _FEAT.sub("", _SUFFIX.sub("", _BRACKETS.sub("", text)))
    text = text.replace("&", " and ")
    return _NON_WORD.sub(" ", text).strip()


def same_artist(a: str, b: str) -> bool:
    a, b = normalize(a), normalize(b)
    return bool(a and b) and (a == b or a in b or b in a)


def same_song(artist_a: str, title_a: str, artist_b: str, title_b: str) -> bool:
    return normalize(title_a) == normalize(title_b) and same_artist(artist_a, artist_b)
