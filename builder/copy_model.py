"""Page copy schema, intake defaults, and an offline draft generator."""

from pydantic import BaseModel, Field


class Item(BaseModel):
    title: str
    text: str


class Service(BaseModel):
    title: str
    text: str
    detail: str = Field(description="Session length, fee or format; empty if unknown")


class Faq(BaseModel):
    question: str
    answer: str


class PageCopy(BaseModel):
    hero_headline: str
    hero_subhead: str
    cta_label: str
    about_title: str
    about_body: str = Field(description="Two short paragraphs separated by a blank line")
    approach_title: str
    approach_intro: str
    approaches: list[Item]
    services_title: str
    services: list[Service]
    process_title: str
    steps: list[Item]
    faq_title: str
    faqs: list[Faq]
    contact_title: str
    contact_body: str
    meta_description: str


# Sections the visitor sees between the hero and the footer, in default order.
SECTIONS = {
    "about": "Über mich",
    "approach": "Arbeitsweise",
    "services": "Angebot",
    "process": "Ablauf",
    "faq": "Häufige Fragen",
    "contact": "Kontakt",
}

LANGUAGES = {"de": "Deutsch", "en": "English"}

SPECIALTIES = [
    "Anxiety", "Depression", "Trauma", "Burnout", "Relationships",
    "Grief", "Self-esteem", "ADHD", "Eating disorders", "Life transitions",
]
METHODS = [
    "CBT", "Schema therapy", "EMDR", "Psychodynamic", "Systemic",
    "ACT", "Mindfulness-based", "Person-centred",
]
AUDIENCES = ["Adults", "Couples", "Young adults", "Teenagers", "Families"]
FORMATS = ["In person", "Online", "Walk & talk"]
TONES = {
    "warm": "Warm und persönlich",
    "calm": "Ruhig und professionell",
    "direct": "Klar und direkt",
}

# German labels for the intake's fixed options, used on German pages.
TERMS_DE = {
    "Anxiety": "Ängste", "Depression": "Depression", "Trauma": "Trauma",
    "Burnout": "Erschöpfung und Burnout", "Relationships": "Beziehungen",
    "Grief": "Trauer", "Self-esteem": "Selbstwert", "ADHD": "ADHS",
    "Eating disorders": "Essstörungen", "Life transitions": "Umbruchphasen",
    "CBT": "Verhaltenstherapie", "Schema therapy": "Schematherapie", "EMDR": "EMDR",
    "Psychodynamic": "Tiefenpsychologie", "Systemic": "Systemische Therapie",
    "ACT": "ACT", "Mindfulness-based": "Achtsamkeitsbasiert",
    "Person-centred": "Personzentriert",
    "Adults": "Erwachsene", "Couples": "Paare", "Young adults": "Junge Erwachsene",
    "Teenagers": "Jugendliche", "Families": "Familien",
    "In person": "In der Praxis", "Online": "Online", "Walk & talk": "Walk & Talk",
}


def localize(terms: list[str], lang: str) -> list[str]:
    return [TERMS_DE.get(t, t) for t in terms] if lang == "de" else list(terms)


EMERGENCY_DEFAULT = {
    "de": "In einer akuten Krise erreichen Sie die Telefonseelsorge rund um die Uhr "
    "unter 0800 111 0 111. Im Notfall wählen Sie 112.",
    "en": "If you are in crisis, call your local emergency number. In the US, call or "
    "text 988 for the Suicide & Crisis Lifeline.",
}

EXAMPLE_INTAKE = {
    "practice_name": "Praxis am Kanal",
    "therapist_name": "Dr. Miriam Albers",
    "credentials": "Psychologische Psychotherapeutin (Verhaltenstherapie)",
    "city": "Hamburg-Eppendorf",
    "language": "de",
    "specialties": ["Anxiety", "Burnout", "Life transitions"],
    "methods": ["CBT", "Schema therapy", "ACT"],
    "audience": ["Adults", "Young adults"],
    "formats": ["In person", "Online"],
    "fees": "Gesetzlich und privat Versicherte sowie Selbstzahler. "
    "Selbstzahler: 50 Minuten, 120 €.",
    "about_notes": "15 Jahre Erfahrung, vorher in einer psychosomatischen Klinik. "
    "Arbeitet viel mit Menschen in Umbruchphasen und Erschöpfung. "
    "Kurze Wartezeit für Erstgespräche (ca. 3 Wochen).",
    "tone": "warm",
    "email": "kontakt@praxis-am-kanal.de",
    "phone": "040 123 456 78",
    "address": "Kanalweg 14, 20249 Hamburg",
    "hours": "Mo–Fr, 8–18 Uhr. Telefonische Sprechzeit Di und Do, 12–13 Uhr.",
    "booking_url": "",
    "emergency_note": EMERGENCY_DEFAULT["de"],
    "imprint_url": "",
    "privacy_url": "",
}


def _join(items: list[str], lang: str) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    word = " und " if lang == "de" else " and "
    return ", ".join(items[:-1]) + word + items[-1]


def draft_copy(intake: dict) -> PageCopy:
    """Template copy built only from intake facts, for use without an API key."""
    de = intake.get("language") == "de"
    lang = "de" if de else "en"
    name = intake.get("therapist_name") or ("Ihre Therapeutin" if de else "your therapist")
    city = intake.get("city") or ""
    focus = _join([s if de else s.lower() for s in localize(intake.get("specialties", []), lang)], lang)
    methods = localize(intake.get("methods", []), lang)
    formats = _join(localize(intake.get("formats", []), lang), lang)
    fees = intake.get("fees", "")

    if de:
        return PageCopy(
            hero_headline="Psychotherapie, die mit Ihrem Alltag beginnt",
            hero_subhead=(
                f"{name} begleitet Erwachsene in {city}. Schwerpunkte: {focus}." if focus
                else f"{name} begleitet Erwachsene in {city}."
            ),
            cta_label="Erstgespräch anfragen",
            about_title=f"Über {name}",
            about_body=(
                f"{intake.get('about_notes', '')}\n\n"
                f"{intake.get('credentials', '')}. Termine: {formats}."
            ).strip(),
            approach_title="Wie ich arbeite",
            approach_intro="Welche Methode passt, entscheiden wir gemeinsam nach dem Erstgespräch.",
            approaches=[Item(title=m, text="Wird im Erstgespräch erklärt.") for m in methods],
            services_title="Angebot",
            services=[
                Service(title="Erstgespräch", text="Wir lernen uns kennen und klären Ihr Anliegen.", detail="50 Minuten"),
                Service(title="Einzeltherapie", text="Regelmäßige Sitzungen im vereinbarten Rhythmus.", detail="50 Minuten"),
            ],
            process_title="So geht es los",
            steps=[
                Item(title="Kontakt aufnehmen", text="Per Telefon oder E-Mail."),
                Item(title="Erstgespräch", text="Wir klären Ihr Anliegen und offene Fragen."),
                Item(title="Therapie beginnen", text="Wir vereinbaren Ziele und einen Rhythmus."),
            ],
            faq_title="Häufige Fragen",
            faqs=[
                Faq(question="Wer übernimmt die Kosten?", answer=fees or "Bitte fragen Sie nach."),
                Faq(question="Wie lange muss ich auf einen Termin warten?", answer="Melden Sie sich, ich nenne Ihnen den nächsten freien Termin."),
            ],
            contact_title="Kontakt",
            contact_body="Schreiben Sie mir oder rufen Sie in der Sprechzeit an.",
            meta_description=f"Psychotherapie in {city}: {name}.",
        )
    return PageCopy(
        hero_headline="Therapy that starts where you are",
        hero_subhead=(
            f"{name} works with adults in {city} on {focus}." if focus
            else f"{name} works with adults in {city}."
        ),
        cta_label="Request a first session",
        about_title=f"About {name}",
        about_body=(
            f"{intake.get('about_notes', '')}\n\n"
            f"{intake.get('credentials', '')}. Sessions {formats.lower()}."
        ).strip(),
        approach_title="How I work",
        approach_intro="We choose the approach together after the first session.",
        approaches=[Item(title=m, text="Explained in the first session.") for m in methods],
        services_title="Services",
        services=[
            Service(title="First session", text="We get to know each other and talk about what brings you.", detail="50 minutes"),
            Service(title="Individual therapy", text="Regular sessions at a pace we agree on.", detail="50 minutes"),
        ],
        process_title="Getting started",
        steps=[
            Item(title="Get in touch", text="By phone or email."),
            Item(title="First session", text="We talk about what brings you and answer your questions."),
            Item(title="Begin therapy", text="We agree on goals and a rhythm."),
        ],
        faq_title="Questions",
        faqs=[
            Faq(question="How much does it cost?", answer=fees or "Please ask."),
            Faq(question="How soon can I start?", answer="Get in touch and I'll tell you the next free slot."),
        ],
        contact_title="Contact",
        contact_body="Write to me or call during phone hours.",
        meta_description=f"Therapy in {city} with {name}.",
    )
