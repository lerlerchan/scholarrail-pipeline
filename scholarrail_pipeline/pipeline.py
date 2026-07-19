"""scholarstack-pipeline — manuscript stages 4-10 runner (PRD §5).

Clean-room MIT implementation designed from the ScholarStack PRD stage list.
Sequential stage drafting, grounded in LightRAG, citations restricted to the
Stage-1.25 verified pool, integrity checks non-skippable, human confirmation
between stages unless --auto.

Usage:
  .venv/bin/python pipeline.py <workdir> [--auto] [--from STAGE]

<workdir> must contain:
  spine.json     — /load-spine output (contribution, blueprint, ...)
  verified.json  — citation_verifier output
Outputs per stage: <workdir>/manuscript/<NN>_<stage>.md, then paper.tex/pdf.

"""
import json
import logging
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from .citations import check_citations  # noqa: F401 (extract kept in citations)
from .llm import chat
from .stages import DRAFT_STAGES, PEER_REVIEW_PROMPT

logger = logging.getLogger(__name__)

LIGHTRAG = "http://localhost:9621"
AUDIT_LOG = Path.home() / "scholarstack" / "logs" / "audit.jsonl"
MAX_REDRAFTS = 2  # bounded Ralph loop per stage


def audit(record: dict) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    record["ts"] = datetime.now(timezone.utc).isoformat()
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")


def grounded_context(query: str) -> str:
    r = requests.post(f"{LIGHTRAG}/query",
                      json={"query": query, "mode": "hybrid",
                            "only_need_context": True},
                      timeout=180)
    r.raise_for_status()
    return r.json().get("response", "")


def draft_stage(name: str, template: str, spine: dict, pool: set[str],
                prior: str) -> str:
    """Draft one stage; re-draft up to MAX_REDRAFTS on citation violation."""
    context = grounded_context(f"{name}: {spine['contribution'][:500]}")
    prompt = template.format(pool=", ".join(sorted(pool)) or "(none)") + (
        f"\n\nCONFIRMED CONTRIBUTION:\n{spine['contribution']}\n\n"
        f"SECTION BLUEPRINT:\n{spine.get('blueprint', '(none)')}\n\n"
        f"MANUSCRIPT SO FAR:\n{prior[-20000:] or '(first section)'}\n\n"
        f"GROUNDED SOURCE MATERIAL (only factual basis):\n{context}\n\n"
        f"Write the section now in Markdown."
    )
    for attempt in range(1 + MAX_REDRAFTS):
        text = chat(prompt, model="deepseek-v4-pro", temperature=0.4)
        bad = check_citations(text, pool)
        audit({"gate": "stage_citation_check", "stage": name,
               "attempt": attempt, "pass": not bad, "violations": bad})
        if not bad:
            return text
        prompt += (f"\n\nPREVIOUS ATTEMPT REJECTED: it cited keys outside the "
                   f"verified pool: {bad}. Remove or replace those citations.")
    raise RuntimeError(f"stage {name}: citation violations after "
                       f"{MAX_REDRAFTS} re-drafts: {bad}")


def assemble(workdir: Path, order: list[str]) -> Path:
    """Concatenate sections in reading order, pandoc → tex, tectonic → pdf."""
    mdir = workdir / "manuscript"
    reading = ["abstract", "introduction", "literature_review", "methodology",
               "results", "discussion", "conclusion"]
    parts = []
    for sec in reading:
        f = next(mdir.glob(f"*_{sec}.md"), None)
        if f:
            parts.append(f"# {sec.replace('_', ' ').title()}\n\n{f.read_text()}")
    md = mdir / "paper.md"
    md.write_text("\n\n".join(parts))
    tex = mdir / "paper.tex"
    subprocess.run(["pandoc", str(md), "-s", "-o", str(tex)], check=True)
    subprocess.run(["tectonic", str(tex)], cwd=mdir, check=True,
                   capture_output=True)
    return mdir / "paper.pdf"


def run(workdir: str, auto: bool = False, start_from: str | None = None) -> Path:
    wd = Path(workdir)
    spine = json.loads((wd / "spine.json").read_text())
    pool = {v["key"] for v in
            json.loads((wd / "verified.json").read_text())["verified"]}
    mdir = wd / "manuscript"
    mdir.mkdir(exist_ok=True)

    prior = ""
    skipping = bool(start_from)
    for i, (name, template) in enumerate(DRAFT_STAGES, 1):
        out = mdir / f"{i:02d}_{name}.md"
        if skipping:
            if name == start_from:
                skipping = False
            else:
                prior += "\n\n" + out.read_text() if out.exists() else ""
                continue
        logger.info("stage %d/%d: %s", i, len(DRAFT_STAGES), name)
        text = draft_stage(name, template, spine, pool, prior)
        out.write_text(text)
        prior += "\n\n" + text
        if not auto:
            input(f"[{name}] written to {out}. Enter to continue, Ctrl-C to stop: ")

    # peer-review simulation (informative, always runs)
    review = chat(PEER_REVIEW_PROMPT.format(manuscript=prior[-60000:]),
                  model="deepseek-v4-pro")
    (mdir / "peer_review_simulation.md").write_text(review)
    audit({"gate": "peer_review_sim", "stage": "post-draft", "pass": True})

    pdf = assemble(wd, [n for n, _ in DRAFT_STAGES])
    audit({"gate": "assembly", "pdf": str(pdf), "pass": pdf.exists()})
    return pdf


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = sys.argv[1:]
    auto = "--auto" in args
    start = args[args.index("--from") + 1] if "--from" in args else None
    print(run(args[0], auto=auto, start_from=start))
