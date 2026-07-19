"""Manuscript stage definitions — clean-room design from ScholarStack PRD §5.

Each stage: name, prompt template, whether it drafts prose (grounded in the
knowledge graph, citations restricted to the verified pool) or runs a
special step (peer-review simulation, assembly).

Placeholders available to templates: {contribution}, {blueprint},
{prior_sections} (accumulated manuscript so far), {context} (LightRAG
retrieval), {pool} (allowed citation keys).
"""

COMMON_RULES = """
Rules:
- Cite only these verified keys, format [@key]: {pool}
- No factual claim absent from the grounded source material.
- Serve the confirmed contribution; academic register; no AI-marker phrases.
"""

DRAFT_STAGES = [
    ("literature_review",
     "Write the Literature Review. Organize around the gap the contribution "
     "fills; synthesize sources, do not summarize them serially." + COMMON_RULES),
    ("methodology",
     "Write the Methodology. Justify each design choice against the "
     "contribution's claim boundary; enough detail to replicate." + COMMON_RULES),
    ("results",
     "Write the Results. Every subsection must validate a contribution "
     "promise; report numbers only from the grounded material." + COMMON_RULES),
    ("discussion",
     "Write the Discussion. Interpret results against the literature; state "
     "limitations honestly; no claims beyond the evidence." + COMMON_RULES),
    ("conclusion",
     "Write the Conclusion. Restate contribution as validated, future work." + COMMON_RULES),
    ("introduction",
     "Write the Introduction last, knowing the full manuscript: problem, gap, "
     "contribution statement, paper roadmap." + COMMON_RULES),
    ("abstract",
     "Write the Abstract (<=250 words): problem, method, key result, "
     "implication. Every claim must be traceable to the manuscript body." + COMMON_RULES),
]

PEER_REVIEW_PROMPT = """Simulate peer review of the manuscript below for a
Scopus-indexed venue. Produce three independent reviews (R1 methods-focused,
R2 novelty-focused, R3 clarity-focused): summary, strengths, weaknesses,
verdict (accept / minor / major / reject). Be adversarial and specific.

MANUSCRIPT:
{manuscript}"""
