"""Generate landing page copy with Claude."""

import json

import anthropic

from .copy_model import LANGUAGES, TONES, PageCopy

MODEL = "claude-opus-5-5"

SYSTEM = """You write landing page copy for psychotherapy and counselling practices.

Readers are often anxious, tired, or unsure whether therapy is for them. Write so
they can understand the page in one calm read: plain words, short sentences, no
jargon without a one-line explanation, no marketing superlatives.

Rules that protect the reader and the therapist:
- Use only facts from the intake. Never invent credentials, years of experience,
  insurance arrangements, fees, waiting times, or locations. If a fact is missing,
  write around it rather than guessing.
- No promises of outcomes or cures, no "guaranteed", no testimonials or quotes from
  clients, no diagnosing the reader.
- Avoid therapy-website cliches: "journey", "safe space", "holistic", "empower",
  "unlock", "your best self", "you are not alone" as a headline.
- Headlines say something specific to this practice. The CTA says exactly what
  happens when clicked (for example, "Request a first session").
- Approaches: one item per method from the intake, each explained in one or two
  sentences a non-expert understands.
- Services: two to four offerings the intake supports. Put session length, fee or
  format in `detail` only when the intake states it; otherwise leave it empty.
- Steps: three or four real steps from first contact to regular sessions.
- FAQs: four to six questions people actually ask before booking (cost, waiting
  time, what the first session is like, online vs in person, confidentiality),
  answered from intake facts.
- meta_description: under 155 characters.
"""


def generate_copy(intake: dict, api_key: str | None = None) -> PageCopy:
    """Ask Claude for structured page copy. Raises anthropic errors to the caller."""
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    facts = {k: v for k, v in intake.items() if k != "portrait" and v}
    lang = LANGUAGES.get(intake.get("language", "en"), "English")
    tone = TONES.get(intake.get("tone", "warm"), "")

    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "medium"},
        system=SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Write the page in {lang}. Tone: {tone}.\n\n"
                    f"Intake:\n{json.dumps(facts, ensure_ascii=False, indent=2)}"
                ),
            }
        ],
        output_format=PageCopy,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude hat diese Anfrage abgelehnt. Bitte die Angaben anpassen und erneut versuchen.")
    if response.stop_reason == "max_tokens" or response.parsed_output is None:
        raise RuntimeError("Die Texte kamen unvollständig zurück. Bitte erneut versuchen.")
    return response.parsed_output
