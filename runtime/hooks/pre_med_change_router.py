"""R1, pre-generation layer. Looks at what the USER asked, so it catches cases where a
compliant-sounding reply never names the medication (the post-generation guard cannot).
Routes medication-change questions to the prescriber before the model is called."""
import re

MED_TERMS = r"(pill|pills|medication|medicine|dose|doses|tablet|tablets|capsule|pastilla|pastillas|medicina|medicamento|dosis)"
CHANGE_TERMS = (r"(earlier|later|sooner|skip|skipping|double|half|split|extra|another|increase|decrease|"
                r"reduce|cut|instead|switch|stop|saltar|omitir|doble|mitad|adelantar|otra)")
_MED = re.compile(rf"\b{MED_TERMS}\b", re.I)
_CHANGE = re.compile(rf"\b{CHANGE_TERMS}\b", re.I)


def route(user_text, ctx):
    if _MED.search(user_text) and _CHANGE.search(user_text):
        ctx.emit("red_line.R1.pre", prompt_version=ctx.prompt_version)
        return ctx.handoff(to="prescriber", template_id="HT-014")
    return None
