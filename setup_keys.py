"""Interactive API-key setup for ScholarStack.

Prompts for each key (input hidden, blank = keep existing) and writes
~/scholarstack/.env with mode 600. Never prints key values.

Usage: python3 setup_keys.py
"""
import getpass
import os
from pathlib import Path

ENV = Path.home() / "scholarstack" / ".env"

# env var -> (description, also_mirror_as)  — LightRAG reads LLM_BINDING_API_KEY
KEYS = {
    "DEEPSEEK_API_KEY": ("DeepSeek (drafting + extraction) — platform.deepseek.com", "LLM_BINDING_API_KEY"),
    "SEMANTIC_SCHOLAR_API_KEY": ("Semantic Scholar (literature search) — semanticscholar.org/product/api#api-key-form", None),
    "SCOPUS_API_KEY": ("Elsevier Scopus (search/verification) — dev.elsevier.com/apikey/manage", None),
    "ANTHROPIC_API_KEY": ("Anthropic Claude (CritiqueBot) — console.anthropic.com", None),
}


def load_env() -> dict:
    if not ENV.exists():
        return {}
    return dict(line.split("=", 1) for line in ENV.read_text().splitlines()
                if "=" in line and not line.startswith("#"))


def main() -> None:
    env = load_env()
    print(f"ScholarStack key setup — writing to {ENV}\n"
          "Press Enter to keep an existing value; input is hidden.\n")
    for var, (desc, mirror) in KEYS.items():
        state = "set" if env.get(var) or (mirror and env.get(mirror)) else "NOT SET"
        val = getpass.getpass(f"{var} [{state}] — {desc}\n> ").strip()
        if val:
            env[var] = val
            if mirror:
                env[mirror] = val
    ENV.parent.mkdir(parents=True, exist_ok=True)
    ENV.write_text("\n".join(f"{k}={v}" for k, v in env.items()) + "\n")
    os.chmod(ENV, 0o600)
    print(f"\nSaved {len(env)} entries to {ENV} (mode 600).")


if __name__ == "__main__":
    main()
