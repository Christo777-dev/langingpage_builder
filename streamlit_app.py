"""Landingpage-Builder für Therapiepraxen.

Angaben -> Claude schreibt die Texte -> Texte bearbeiten -> Design wählen,
Vorschau ansehen und eine einzelne HTML-Datei herunterladen.
"""

import base64
import copy as copylib
import io
import os
import re

import anthropic
import pandas as pd
import streamlit as st
from PIL import Image

from builder.ai import MODEL, generate_copy
from builder.copy_model import (
    AUDIENCES, EMERGENCY_DEFAULT, EXAMPLE_INTAKE, FORMATS, LANGUAGES, METHODS,
    SECTIONS, SPECIALTIES, TERMS_DE, TONES, draft_copy,
)
from builder.render import render_page
from builder.themes import BUTTON_SHAPES, LAYOUTS, THEMES

st.set_page_config(page_title="Praxis-Seitenbauer", page_icon=":material/spa:", layout="wide")

STEPS = ["Angaben", "Texte", "Design und Export"]
TEXT_FIELDS = [
    "practice_name", "therapist_name", "credentials", "city", "fees", "about_notes",
    "email", "phone", "address", "hours", "booking_url", "emergency_note",
    "imprint_url", "privacy_url",
]
LIST_FIELDS = ["specialties", "methods", "audience", "formats"]


def de(term: str) -> str:
    return TERMS_DE.get(term, term)


ss = st.session_state
ss.setdefault("copy", None)
ss.setdefault("rev", 0)
ss.setdefault("order", list(SECTIONS))
ss.setdefault("visible", {k: True for k in SECTIONS})
ss.setdefault("portrait", None)
ss.setdefault("step", STEPS[0])
ss.setdefault("last_step", None)
for f in TEXT_FIELDS:
    ss.setdefault(f"in_{f}", "")
for f in LIST_FIELDS:
    ss.setdefault(f"in_{f}", [])
ss.setdefault("in_language", "de")
ss.setdefault("in_tone", "warm")
ss.setdefault("in_emergency_note", EMERGENCY_DEFAULT["de"])
if "goto" in ss:
    ss.step = ss.pop("goto")


def intake() -> dict:
    data = {f: ss[f"in_{f}"] for f in TEXT_FIELDS + LIST_FIELDS}
    data["language"] = ss.in_language
    data["tone"] = ss.in_tone
    data["portrait"] = ss.portrait
    return data


def fill_example() -> None:
    for k, v in EXAMPLE_INTAKE.items():
        ss[f"in_{k}"] = v


def api_key() -> str | None:
    if ss.get("api_key"):
        return ss.api_key
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    try:
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        return None


def portrait_data_uri(upload) -> str:
    img = Image.open(upload).convert("RGB")
    img.thumbnail((900, 1100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def use_copy(new_copy: dict) -> None:
    ss.copy = new_copy
    ss.rev += 1
    ss.goto = STEPS[1]


def move(idx: int, delta: int) -> None:
    order = ss.order
    j = idx + delta
    if 0 <= j < len(order):
        order[idx], order[j] = order[j], order[idx]


def records(df: pd.DataFrame, required: str) -> list[dict]:
    rows = df.fillna("").astype(str).to_dict("records")
    return [{k: v.strip() for k, v in r.items()} for r in rows if r.get(required, "").strip()]


# --------------------------------------------------------------------------

st.title("Praxis-Seitenbauer")
st.caption(
    "Beschreiben Sie Ihre Praxis, lassen Sie Claude die Seite entwerfen, passen Sie "
    "jedes Wort an und laden Sie am Ende eine fertige HTML-Datei herunter."
)

has_copy = ss.copy is not None
st.segmented_control(
    "Schritt", STEPS, key="step", required=True, label_visibility="collapsed",
    format_func=lambda s: f"{STEPS.index(s) + 1}  {s}",
)
step = ss.step
entering = step != ss.last_step
ss.last_step = step

# ---- 1 Angaben -----------------------------------------------------------

if step == STEPS[0]:
    with st.container(horizontal=True, vertical_alignment="center"):
        st.button("Mit Beispielpraxis ausfüllen", icon=":material/edit_note:", on_click=fill_example)
        if not api_key():
            with st.popover("Claude-API-Key eingeben", icon=":material/key:"):
                st.text_input(
                    "Anthropic-API-Key", type="password", key="api_key", persist_state="session",
                    help="Bleibt nur in dieser Browsersitzung. Alternativ die Umgebungsvariable "
                    "ANTHROPIC_API_KEY setzen oder den Key in .streamlit/secrets.toml eintragen.",
                )

    with st.form("intake", border=False):
        st.subheader("Die Praxis")
        c1, c2 = st.columns(2)
        c1.text_input("Name der Praxis", key="in_practice_name", persist_state="page", placeholder="Praxis am Kanal")
        c2.text_input("Name der Therapeutin oder des Therapeuten", key="in_therapist_name", persist_state="page",
                      placeholder="Dr. Miriam Albers")
        c1.text_input("Qualifikation", key="in_credentials", persist_state="page",
                      placeholder="Psychologische Psychotherapeutin (Verhaltenstherapie)")
        c2.text_input("Ort oder Stadtteil", key="in_city", persist_state="page", placeholder="Hamburg-Eppendorf")
        st.text_area(
            "Über die Person", key="in_about_notes", persist_state="page", height=110,
            placeholder="Werdegang, Erfahrung, mit wem Sie besonders gern arbeiten, Wartezeiten.",
        )
        st.file_uploader("Porträtfoto (optional)", type=["jpg", "jpeg", "png", "webp"], key="in_portrait_file")

        st.subheader("Die Arbeit")
        st.pills("Schwerpunkte", SPECIALTIES, selection_mode="multi", key="in_specialties",
                 persist_state="page", format_func=de)
        st.pills("Methoden", METHODS, selection_mode="multi", key="in_methods",
                 persist_state="page", format_func=de)
        c1, c2 = st.columns(2)
        with c1:
            st.pills("Arbeitet mit", AUDIENCES, selection_mode="multi", key="in_audience",
                     persist_state="page", format_func=de)
        with c2:
            st.pills("Format der Sitzungen", FORMATS, selection_mode="multi", key="in_formats",
                     persist_state="page", format_func=de)
        st.text_input("Kosten und Kassen", key="in_fees", persist_state="page",
                      placeholder="Gesetzlich und privat Versicherte; Selbstzahler 50 Min., 120 €")

        st.subheader("Kontakt")
        c1, c2 = st.columns(2)
        c1.text_input("E-Mail", key="in_email", persist_state="page")
        c2.text_input("Telefon", key="in_phone", persist_state="page")
        c1.text_area("Adresse", key="in_address", persist_state="page", height=80)
        c2.text_area("Sprechzeiten", key="in_hours", persist_state="page", height=80)
        st.text_input("Link zur Online-Terminbuchung (optional)", key="in_booking_url", persist_state="page",
                      help="Bleibt das Feld leer, führt der Hauptbutton zum Kontaktbereich der Seite.")
        st.text_area("Hinweis für Notfälle", key="in_emergency_note", persist_state="page", height=80,
                     help="Steht in der Nähe der Kontaktdaten. Bitte die Nummern für Ihr Land prüfen.")
        c1, c2 = st.columns(2)
        c1.text_input("Link zum Impressum (optional)", key="in_imprint_url", persist_state="page")
        c2.text_input("Link zur Datenschutzerklärung (optional)", key="in_privacy_url", persist_state="page")

        st.subheader("Tonfall")
        c1, c2 = st.columns(2)
        with c1:
            st.segmented_control("Sprache der Seite", list(LANGUAGES), key="in_language", persist_state="page",
                                 format_func=LANGUAGES.get, required=True)
        with c2:
            st.segmented_control("Tonfall", list(TONES), key="in_tone", persist_state="page",
                                 format_func=TONES.get, required=True)

        with st.container(horizontal=True):
            write = st.form_submit_button("Texte von Claude schreiben lassen", type="primary",
                                          icon=":material/auto_awesome:")
            draft = st.form_submit_button("Vorlage verwenden", icon=":material/description:",
                                          help="Füllt die Seite aus Ihren Angaben, ohne Claude zu fragen.")

    if write or draft:
        upload = ss.get("in_portrait_file")
        if upload is not None:
            ss.portrait = portrait_data_uri(upload)
        data = intake()
        if not data["practice_name"] or not data["therapist_name"]:
            st.error("Bitte tragen Sie den Namen der Praxis und der Person ein und versuchen Sie es erneut.")
        elif draft:
            use_copy(draft_copy(data).model_dump())
            st.rerun()
        elif not api_key():
            st.error("Bitte zuerst einen Claude-API-Key eingeben oder die Vorlage verwenden.",
                     icon=":material/key_off:")
        else:
            try:
                with st.spinner(f"Claude ({MODEL}) schreibt die Seite …"):
                    result = generate_copy(data, api_key())
            except anthropic.AuthenticationError:
                st.error("Der API-Key wurde abgelehnt. Bitte prüfen und erneut versuchen.")
            except anthropic.RateLimitError:
                st.error("Zu viele Anfragen in kurzer Zeit. Bitte eine Minute warten und erneut versuchen.")
            except anthropic.APIConnectionError:
                st.error("Die Claude-API ist nicht erreichbar. Bitte die Internetverbindung prüfen.")
            except anthropic.APIStatusError as err:
                st.error(f"Die Claude-API meldet einen Fehler ({err.status_code}): {err.message}")
            except RuntimeError as err:
                st.error(str(err))
            else:
                use_copy(result.model_dump())
                st.rerun()

# ---- 2 Texte -------------------------------------------------------------

elif step == STEPS[1]:
    if not has_copy:
        st.info("Füllen Sie zuerst die Angaben aus. Die Texte erscheinen hier, sobald sie geschrieben sind.",
                icon=":material/arrow_back:")
        st.stop()
    if entering:
        ss.rev += 1
        ss.base = copylib.deepcopy(ss.copy)
    ss.setdefault("base", copylib.deepcopy(ss.copy))
    base, r = ss.base, ss.rev
    new = {}

    def txt(field: str, label: str, area: bool = False, height: int = 100) -> None:
        if area:
            new[field] = st.text_area(label, base.get(field, ""), key=f"{field}_{r}", height=height)
        else:
            new[field] = st.text_input(label, base.get(field, ""), key=f"{field}_{r}")

    def table(field: str, label: str, cols: dict[str, str], required: str) -> None:
        df = pd.DataFrame(base.get(field, []), columns=list(cols))
        edited = st.data_editor(
            df, key=f"{field}_{r}", num_rows="dynamic", hide_index=True,
            column_config={k: st.column_config.TextColumn(v, width="large" if k in ("text", "answer") else "medium")
                           for k, v in cols.items()},
            alt=label,
        )
        new[field] = records(edited, required)

    st.caption("Alles hier erscheint genau so auf der Seite. Ändern Sie, was Sie möchten.")
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.subheader("Einstieg")
            txt("hero_headline", "Überschrift")
            txt("hero_subhead", "Unterzeile", area=True, height=80)
            txt("cta_label", "Hauptbutton")
            txt("meta_description", "Beschreibung für Suchmaschinen", area=True, height=68)
        with st.container(border=True):
            st.subheader("Über mich")
            txt("about_title", "Überschrift")
            txt("about_body", "Text", area=True, height=220)
        with st.container(border=True):
            st.subheader("Kontakt")
            txt("contact_title", "Überschrift")
            txt("contact_body", "Text", area=True, height=80)
    with right:
        with st.container(border=True):
            st.subheader("Arbeitsweise")
            txt("approach_title", "Überschrift")
            txt("approach_intro", "Einleitung", area=True, height=68)
            table("approaches", "Methoden", {"title": "Methode", "text": "Erklärung"}, "title")
        with st.container(border=True):
            st.subheader("Angebot")
            txt("services_title", "Überschrift")
            table("services", "Angebot", {"title": "Leistung", "text": "Beschreibung", "detail": "Dauer oder Preis"},
                  "title")
        with st.container(border=True):
            st.subheader("Ablauf")
            txt("process_title", "Überschrift")
            table("steps", "Schritte", {"title": "Schritt", "text": "Was passiert"}, "title")
        with st.container(border=True):
            st.subheader("Häufige Fragen")
            txt("faq_title", "Überschrift")
            table("faqs", "Fragen", {"question": "Frage", "answer": "Antwort"}, "question")
    ss.copy = new

    st.button("Weiter zum Design", type="primary", icon=":material/palette:",
              on_click=lambda: ss.update(goto=STEPS[2]))

# ---- 3 Design und Export -------------------------------------------------

else:
    if not has_copy:
        st.info("Füllen Sie zuerst die Angaben aus. Die Vorschau erscheint, sobald es Texte gibt.",
                icon=":material/arrow_back:")
        st.stop()

    controls, preview = st.columns([1, 2.5], gap="large")
    with controls:
        theme_key = st.radio(
            "Design", list(THEMES), key="theme", persist_state="page",
            format_func=lambda k: THEMES[k].name,
            captions=[t.blurb for t in THEMES.values()],
        )
        theme = THEMES[theme_key]

        with st.expander("Erweiterte Einstellungen", icon=":material/tune:"):
            layout = st.selectbox(
                "Aufbau", ["default", *LAYOUTS], key="layout", persist_state="page",
                format_func=lambda k: f"Wie im Design ({LAYOUTS[theme.layout]})" if k == "default" else LAYOUTS[k],
                help="Farben und Schriften dieses Designs behalten, aber den Aufbau eines anderen verwenden.",
            )
            shape = st.segmented_control(
                "Form der Buttons", ["default", *BUTTON_SHAPES], key="shape", persist_state="page",
                default="default", required=True,
                format_func=lambda k: "Wie im Design" if k == "default" else BUTTON_SHAPES[k],
            )

            custom = st.toggle("Eigene Farben", key="custom_colors", persist_state="page")
            colors = {}
            if custom:
                c1, c2 = st.columns(2)
                for col, (name, label) in zip(
                    [c1, c2, c1, c2],
                    [("bg", "Hintergrund"), ("ink", "Text"), ("accent", "Akzent"), ("soft", "Tönung")],
                ):
                    with col:
                        colors[name] = st.color_picker(
                            label, getattr(theme, name), key=f"col_{theme_key}_{name}",
                            persist_state="page",
                        )

            st.markdown("**Bereiche**")
            st.caption("Einstieg und Fußzeile bleiben immer an ihrem Platz.")
            for idx, key in enumerate(ss.order):
                with st.container(horizontal=True, vertical_alignment="center", gap="xsmall"):
                    ss.visible[key] = st.checkbox(
                        SECTIONS[key], value=ss.visible[key], key=f"show_{key}", width="stretch",
                    )
                    st.button(":material/arrow_upward:", key=f"up_{key}", help="Nach oben",
                              disabled=idx == 0, on_click=move, args=(idx, -1), type="tertiary")
                    st.button(":material/arrow_downward:", key=f"down_{key}", help="Nach unten",
                              disabled=idx == len(ss.order) - 1, on_click=move, args=(idx, 1),
                              type="tertiary")

        order = [k for k in ss.order if ss.visible[k]]
        page = render_page(
            ss.copy, intake(), theme_key,
            layout=None if layout == "default" else layout,
            colors=colors if custom else None,
            button_shape=None if shape == "default" else shape,
            order=order,
        )
        slug = re.sub(r"[^a-z0-9]+", "-", (ss.in_practice_name or "praxis").lower()).strip("-")
        st.download_button(
            "HTML herunterladen", page, file_name=f"{slug}-{theme_key}.html", mime="text/html",
            type="primary", icon=":material/download:", width="stretch",
        )
        st.caption(f"Eine Datei, {len(page.encode()) // 1024} KB. Die Schriften lädt die Seite von Google Fonts.")

    with preview:
        device = st.segmented_control(
            "Vorschaubreite", ["Computer", "Handy"], default="Computer", required=True,
            key="device", persist_state="page", label_visibility="collapsed",
        )
        # All copy is HTML-escaped by render_page and the page carries no scripts.
        st.iframe(page, height=860, width="stretch" if device == "Computer" else 390,
                  alt=f"Vorschau der Seite im Design {theme.name}")
