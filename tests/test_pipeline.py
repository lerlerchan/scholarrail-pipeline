"""Pipeline tests. Unit tier offline (chat + retrieval monkeypatched).

Integration tier: single-stage live run + assembly to PDF.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from scholarrail_pipeline import pipeline, stages


def _setup_workdir(tmp_path):
    (tmp_path / "spine.json").write_text(json.dumps(
        {"contribution": "We contribute an AHP-weighted GBQ instrument.",
         "blueprint": "| section | goal |"}))
    (tmp_path / "verified.json").write_text(json.dumps(
        {"verified": [{"key": "tan2023gbq"}], "rejected": []}))
    return tmp_path


# ---------- unit ----------

def test_stage_redraft_on_violation_then_success(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "AUDIT_LOG", tmp_path / "audit.jsonl")
    monkeypatch.setattr(pipeline, "grounded_context", lambda q: "GBQ material")
    answers = iter(["bad [@fake2020]", "good [@tan2023gbq]"])
    monkeypatch.setattr(pipeline, "chat", lambda *a, **k: next(answers))
    text = pipeline.draft_stage("results", stages.DRAFT_STAGES[2][1],
                                {"contribution": "c"}, {"tan2023gbq"}, "")
    assert "good" in text
    lines = [json.loads(l) for l in
             (tmp_path / "audit.jsonl").read_text().splitlines()]
    assert [l["pass"] for l in lines] == [False, True]


def test_stage_hard_fails_after_bounded_redrafts(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "AUDIT_LOG", tmp_path / "audit.jsonl")
    monkeypatch.setattr(pipeline, "grounded_context", lambda q: "x")
    monkeypatch.setattr(pipeline, "chat", lambda *a, **k: "always [@fake]")
    with pytest.raises(RuntimeError, match="citation violations"):
        pipeline.draft_stage("results", stages.DRAFT_STAGES[2][1],
                             {"contribution": "c"}, {"real"}, "")


def test_full_run_offline(tmp_path, monkeypatch):
    wd = _setup_workdir(tmp_path)
    monkeypatch.setattr(pipeline, "AUDIT_LOG", tmp_path / "audit.jsonl")
    monkeypatch.setattr(pipeline, "grounded_context", lambda q: "GBQ material")
    monkeypatch.setattr(pipeline, "chat",
                        lambda *a, **k: "Section text [@tan2023gbq].")
    pdf = pipeline.run(str(wd), auto=True)
    assert pdf.exists() and pdf.stat().st_size > 1000
    mds = sorted(p.name for p in (wd / "manuscript").glob("0*_*.md"))
    assert len(mds) == len(stages.DRAFT_STAGES)
    assert (wd / "manuscript" / "peer_review_simulation.md").exists()


# ---------- integration (live LightRAG + DeepSeek, ~1 stage) ----------

@pytest.mark.integration
def test_single_stage_live(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "AUDIT_LOG", tmp_path / "audit.jsonl")
    spine = {"contribution": "We contribute an AHP-weighted GBQ instrument "
                             "for postgraduate green behaviour."}
    text = pipeline.draft_stage("literature_review",
                                stages.DRAFT_STAGES[0][1],
                                spine, {"tan2023gbq"}, "")
    assert len(text) > 300
    assert pipeline.check_citations(text, {"tan2023gbq"}) == []
