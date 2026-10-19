"""One turn: pre hooks -> model -> schema -> post hooks. The model is injected so
the whole path is testable offline with recorded outputs."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from runtime.hooks.post_red_line_guard import post_red_line_guard
from runtime.hooks.post_ui_validator import post_ui_validator
from runtime.hooks.pre_crisis_router import route
from runtime.hooks.pre_disclosure_router import route as disclosure_route
from runtime.hooks.pre_med_change_router import route as med_route
from runtime.hooks.pre_phi_mask import mask
from runtime.routing import route_intent

SCHEMA = json.loads((Path(__file__).parent / "schemas" / "ui_response.schema.json").read_text())


def run_turn(user_text, ctx, model, classify=None):
    crisis = route(user_text, ctx)
    if crisis:
        return crisis
    med_change = med_route(user_text, ctx)
    if med_change:
        return med_change
    disclosed = disclosure_route(user_text, ctx)
    if disclosed:
        return disclosed
    masked, _ = mask(user_text)
    if classify is not None:  # prompt-library intent_classifier; the model labels, routing.json decides
        routed = route_intent(classify(masked), ctx)
        if routed:
            return routed
    resp = model(masked)
    if list(Draft202012Validator(SCHEMA).iter_errors(resp)):
        return ctx.fallback(template_id="FB-001")
    resp = post_ui_validator(resp, ctx, model)
    return post_red_line_guard(resp, ctx)
