"""Mechanical [@key] citation checking — the pipeline's core guarantee."""
import re

CITE_RE = re.compile(r"\[@([^\]]+)\]")


def extract_citations(text: str) -> set[str]:
    return {c.strip() for c in CITE_RE.findall(text)}


def check_citations(draft: str, pool: set[str]) -> list[str]:
    """Return citation keys used in draft that are NOT in the verified pool."""
    return sorted(extract_citations(draft) - pool)
