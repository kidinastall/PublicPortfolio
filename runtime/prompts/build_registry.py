"""Regenerate library/registry.json from module frontmatter. Run: python3 -m runtime.prompts.build_registry"""
import json

from runtime.prompts.loader import LIB, load, modules, tokens


def build():
    rows = []
    for mid in modules():
        meta, body = load(mid)
        rows.append({**{k: meta[k] for k in ("id", "version", "kind", "status", "owner_role", "model_tier", "output", "eval")},
                     "max_tokens": meta["max_tokens"], "tokens": tokens(body)})
    (LIB / "registry.json").write_text(json.dumps({"modules": rows}, indent=2) + "\n")
    return rows


if __name__ == "__main__":
    for r in build():
        print(f"{r['id']:<22} v{r['version']}  {r['tokens']:>3}/{r['max_tokens']} tokens  {r['model_tier']}")
