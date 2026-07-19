"""scholarrail-pipeline — grounded manuscript drafting with mechanical citation gates."""
from .citations import check_citations, extract_citations
from .llm import chat
from .pipeline import run

__all__ = ["check_citations", "extract_citations", "chat", "run"]
__version__ = "0.1.0"
