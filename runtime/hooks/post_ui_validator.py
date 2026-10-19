"""Design-system invariant: a component, prop or time slot the design system never
issued is repaired once, or replaced by a fixed fallback. Never rendered."""
import difflib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator

TOKENS = json.loads((Path(__file__).resolve().parents[2] / "design-system" / "design_tokens.json").read_text())
COMPONENTS, ALIASES = TOKENS["components"], TOKENS["aliases"]
FORBIDDEN = re.compile("|".join(TOKENS["forbidden_terms"]), re.I)
DOSE_VALUE = re.compile(r"\b\d+(\.\d+)?\s?(mg|mcg|ml)\b", re.I)
MAX_REPAIRS = 1


def check(resp, ctx):
    errors, red_line = [], False
    for i, c in enumerate(resp["components"]):
        name = ALIASES.get(c.get("type"), c.get("type"))
        props = c.get("props", {})
        spec = COMPONENTS.get(name)
        if spec is None:
            near = difflib.get_close_matches(name, COMPONENTS, n=2, cutoff=0.3)
            tag = " (R1-suspect name)" if FORBIDDEN.search(name) else ""
            errors.append(f"components[{i}]: '{name}' is not in design system "
                          f"v{TOKENS['version']}{tag}. Nearest: {near or list(COMPONENTS)}")
            red_line |= any(FORBIDDEN.search(k) for k in props) or bool(DOSE_VALUE.search(json.dumps(props)))
            continue
        c["type"] = name  # alias repair is deterministic and logged by the caller
        schema = {"type": "object", "properties": spec["props"],
                  "required": spec["required"], "additionalProperties": False}
        for e in Draft202012Validator(schema).iter_errors(props):
            errors.append(f"components[{i}] {name}: {e.message}")
        for sid in props.get("slot_ids", []):
            if sid not in ctx.schedule.slot_ids():
                errors.append(f"components[{i}]: slot '{sid}' was not issued by med_schedule.py")
    return errors, red_line


def repair_prompt(errors):
    return ("Your last response failed validation:\n- " + "\n- ".join(errors) +
            f"\nUse only these components: {', '.join(COMPONENTS)}. "
            "Use only slot_ids from the schedule tool result. "
            "Return the complete JSON object again.")


def post_ui_validator(resp, ctx, call_model):
    errors, red_line = check(resp, ctx)
    if not errors:
        return resp
    ctx.emit("ui.contract_violation", errors=errors, red_line=red_line,
             attempt=ctx.repairs, prompt_version=ctx.prompt_version)
    if red_line or ctx.repairs >= MAX_REPAIRS:
        return ctx.fallback(template_id="FB-002")
    ctx.repairs += 1
    return post_ui_validator(call_model(repair_prompt(errors)), ctx, call_model)
