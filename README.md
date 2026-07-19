# scholarstack-pipeline

MIT-licensed manuscript-writing pipeline for [ScholarStack](https://github.com/lerlerchan/ScholarStack) (PRD §5, stages 4–10).

Clean-room implementation designed from the ScholarStack PRD stage list. Not derived from any CC-licensed codebase.

## What it does

Sequential grounded drafting: literature review → methodology → results → discussion → conclusion → introduction → abstract → peer-review simulation → LaTeX/PDF assembly.

Guarantees:
- **Grounded**: every stage retrieves source material from LightRAG (`only_need_context`); the LLM may not claim beyond it.
- **Citation discipline**: `[@key]` citations are checked mechanically after every stage against the Stage-1.25 verified pool; violations trigger bounded re-draft (max 2), then hard failure. Non-skippable.
- **Human gates**: pauses after every stage unless `--auto`.
- **Audited**: every gate result appended to the ScholarStack audit log (JSONL).

## Usage

```bash
python pipeline.py <workdir> [--auto] [--from STAGE]
```

`<workdir>` needs `spine.json` (from ScholarStack `/load-spine`) and `verified.json` (from the Citation Verification Gate). Output: `<workdir>/manuscript/*.md` + `paper.pdf`.

## Requirements

LightRAG server on `localhost:9621`, DeepSeek API key, `pandoc` + `tectonic` on PATH. Models per ScholarStack PRD §4: `deepseek-v4-pro` for drafting.
