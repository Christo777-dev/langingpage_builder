"""Render page copy into a standalone HTML landing page.

Every piece of copy (user-typed or AI-written) passes through `e()` before it
reaches the markup, so the exported file is safe to embed and publish.
"""

import datetime
import html
import re

from .copy_model import SECTIONS, localize
from .themes import BUTTON_SHAPES, THEMES, readable_on

LABELS = {
    "de": {
        "skip": "Zum Inhalt springen", "nav": "Hauptnavigation",
        "about": "Über mich", "approach": "Arbeitsweise", "services": "Angebot",
        "process": "Ablauf", "faq": "Fragen", "contact": "Kontakt",
        "address": "Adresse", "phone": "Telefon", "email": "E-Mail", "hours": "Sprechzeiten",
        "therapist": "Therapie bei", "focus": "Schwerpunkte", "methods": "Methoden",
        "formats": "Format", "fees": "Kosten", "location": "Ort",
        "imprint": "Impressum", "privacy": "Datenschutz", "portrait": "Porträt von",
        "emergency": "Im Notfall",
    },
    "en": {
        "skip": "Skip to content", "nav": "Main navigation",
        "about": "About", "approach": "Approach", "services": "Services",
        "process": "First steps", "faq": "Questions", "contact": "Contact",
        "address": "Address", "phone": "Phone", "email": "Email", "hours": "Hours",
        "therapist": "Therapist", "focus": "Focus", "methods": "Methods",
        "formats": "Format", "fees": "Fees", "location": "Location",
        "imprint": "Imprint", "privacy": "Privacy", "portrait": "Portrait of",
        "emergency": "In an emergency",
    },
}

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def e(value) -> str:
    return html.escape(str(value or ""), quote=True)


def paras(text: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text or "") if b.strip()]
    return "".join(f"<p>{e(b).replace(chr(10), '<br>')}</p>" for b in blocks)


def initials(name: str) -> str:
    words = [w for w in re.split(r"\s+", name or "") if w and not w.endswith(".")]
    return "".join(w[0] for w in words[:2]).upper() or "·"


class Page:
    """Shared facts and helpers handed to a layout."""

    def __init__(self, copy: dict, intake: dict, order: list[str]):
        self.c = copy
        self.i = intake
        self.lang = intake.get("language", "en")
        self.t = LABELS.get(self.lang, LABELS["en"])
        self.order = [s for s in order if s in SECTIONS]
        booking = (intake.get("booking_url") or "").strip()
        self.cta_href = booking if booking.startswith(("http://", "https://")) else "#contact"

    def nav_items(self) -> str:
        return "".join(
            f'<li><a href="#{s}">{e(self.t[s])}</a></li>' for s in self.order
        )

    def nav(self, cls: str = "") -> str:
        return (
            f'<nav class="{cls}" aria-label="{e(self.t["nav"])}">'
            f"<ul>{self.nav_items()}</ul></nav>"
        )

    def btn(self, label: str | None = None, href: str | None = None, extra: str = "") -> str:
        return (
            f'<a class="btn {extra}" href="{e(href or self.cta_href)}">'
            f"<span>{e(label or self.c.get('cta_label'))}</span></a>"
        )

    def portrait(self, cls: str = "photo") -> str:
        src = self.i.get("portrait")
        name = self.i.get("therapist_name", "")
        if src:
            return (
                f'<img class="{cls}" src="{e(src)}" '
                f'alt="{e(self.t["portrait"])} {e(name)}">'
            )
        return f'<div class="monogram" aria-hidden="true">{e(initials(name))}</div>'

    def who(self) -> str:
        parts = [self.i.get("therapist_name"), self.i.get("credentials")]
        return ", ".join(e(p) for p in parts if p)

    def contact_rows(self) -> list[tuple[str, str]]:
        rows = []
        if self.i.get("address"):
            rows.append((self.t["address"], e(self.i["address"]).replace(chr(10), "<br>")))
        if self.i.get("phone"):
            tel = re.sub(r"[^\d+]", "", self.i["phone"])
            rows.append((self.t["phone"], f'<a href="tel:{e(tel)}">{e(self.i["phone"])}</a>'))
        if self.i.get("email"):
            rows.append(
                (self.t["email"], f'<a href="mailto:{e(self.i["email"])}">{e(self.i["email"])}</a>')
            )
        if self.i.get("hours"):
            rows.append((self.t["hours"], e(self.i["hours"])))
        return rows

    def contact_dl(self, cls: str = "") -> str:
        rows = "".join(f"<div><dt>{e(k)}</dt><dd>{v}</dd></div>" for k, v in self.contact_rows())
        return f'<dl class="{cls}">{rows}</dl>'

    def facts(self) -> list[tuple[str, str]]:
        lang = self.lang
        rows = [
            (self.t["therapist"], self.who()),
            (self.t["focus"], e(", ".join(localize(self.i.get("specialties", []), lang)))),
            (self.t["methods"], e(", ".join(localize(self.i.get("methods", []), lang)))),
            (self.t["formats"], e(", ".join(localize(self.i.get("formats", []), lang)))),
            (self.t["location"], e(self.i.get("city"))),
            (self.t["fees"], e(self.i.get("fees"))),
        ]
        return [(k, v) for k, v in rows if v]

    def emergency(self, cls: str = "emergency") -> str:
        note = self.i.get("emergency_note")
        if not note:
            return ""
        return (
            f'<aside class="{cls}" role="note"><strong>{e(self.t["emergency"])}</strong>'
            f"<p>{e(note)}</p></aside>"
        )

    def legal_links(self) -> str:
        links = []
        for key in ("imprint", "privacy"):
            url = (self.i.get(f"{key}_url") or "").strip()
            if url:
                links.append(f'<a href="{e(url)}">{e(self.t[key])}</a>')
        return "".join(links)

    def year(self) -> int:
        return datetime.date.today().year

    def faqs(self, marker: str = "") -> str:
        return "".join(
            f"<details><summary><span>{e(f.get('question'))}</span>{marker}</summary>"
            f"<div class=\"answer\">{paras(f.get('answer'))}</div></details>"
            for f in self.c.get("faqs", [])
        )


# --------------------------------------------------------------------------
# Shared CSS: reset, type defaults, buttons and their shapes, accessibility.
# --------------------------------------------------------------------------

BASE_CSS = """
:root{--muted:color-mix(in srgb,var(--ink) 72%,var(--bg));--line:color-mix(in srgb,var(--ink) 20%,var(--bg));--display-stretch:100%;--btn-r:0}
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:1.0625rem;line-height:1.65;text-rendering:optimizeLegibility;-webkit-font-smoothing:antialiased}
img{max-width:100%;display:block}
a{color:inherit;text-underline-offset:.2em;text-decoration-thickness:1px}
h1,h2,h3{font-family:var(--display);font-weight:var(--display-weight);letter-spacing:var(--display-track);font-stretch:var(--display-stretch);line-height:1.1;margin:0;text-wrap:balance}
p{margin:0 0 1em}p:last-child{margin-bottom:0}
ul,ol,dl,dd{margin:0;padding:0}
:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
.wrap{max-width:74rem;margin-inline:auto;padding-inline:clamp(1.125rem,4vw,2.5rem)}
.skip{position:absolute;left:1rem;top:-5rem;z-index:50;background:var(--ink);color:var(--bg);padding:.7rem 1rem}
.skip:focus{top:1rem}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:3rem;padding:.8em 1.7em;font:600 1rem/1.2 var(--body);text-decoration:none;border:2px solid var(--btn-bg,var(--accent));background:var(--btn-bg,var(--accent));color:var(--btn-fg,var(--accent-ink));border-radius:var(--btn-r);transition:background-color .2s,color .2s}
.btn:hover{background:transparent;color:var(--btn-bg,var(--accent))}
.btn>span{display:inline-block}
.shape-pill{--btn-r:999px}.shape-rounded{--btn-r:.55em}.shape-square{--btn-r:0}
.shape-leaf{--btn-r:1.6em .3em 1.6em .3em}
.btn.shape-slanted{border-radius:0;transform:skewX(-12deg)}.btn.shape-slanted>span{transform:skewX(12deg)}
summary{cursor:pointer;list-style:none}summary::-webkit-details-marker{display:none}
.monogram{display:grid;place-items:center;width:100%;height:100%;font-family:var(--display);line-height:1;user-select:none}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}html{scroll-behavior:auto}}
"""


# --------------------------------------------------------------------------
# Organic flow: breathing blob hero, pebble approaches, a pond for contact.
# --------------------------------------------------------------------------

FLOW_CSS = """
.lay-flow .top{display:flex;align-items:center;justify-content:space-between;gap:1rem 2rem;flex-wrap:wrap;padding-block:1.75rem}
.lay-flow .brand{font-family:var(--display);font-size:1.4rem;text-decoration:none}
.lay-flow nav ul{display:flex;flex-wrap:wrap;gap:.35rem 1.5rem;list-style:none;font-size:.97rem}
.lay-flow nav a{text-decoration:none;color:var(--muted)}.lay-flow nav a:hover{color:var(--ink);text-decoration:underline}
.f-hero{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:clamp(2rem,6vw,6rem);align-items:center;padding-block:clamp(2rem,6vw,4.5rem) clamp(4rem,9vw,8rem)}
.f-hero h1{font-size:clamp(2.6rem,5.8vw,4.75rem);line-height:1.04}
.f-hero .sub{font-size:1.25rem;line-height:1.55;max-width:34ch;margin:1.6rem 0 2.2rem;color:var(--muted)}
.f-hero .who{margin-top:2.2rem;font-style:italic;color:var(--muted);font-size:.97rem;max-width:40ch}
.stage{position:relative;width:min(100%,30rem);aspect-ratio:1/1.06;justify-self:center}
.blob{position:absolute;inset:0;overflow:hidden;border-radius:63% 37% 54% 46%/55% 48% 52% 45%;animation:breathe 18s ease-in-out infinite alternate}
.blob.back{background:color-mix(in srgb,var(--accent) 22%,#fff);transform:translate(8%,7%) rotate(14deg);animation-direction:alternate-reverse}
.blob.front{background:var(--soft)}
.blob img{width:100%;height:100%;object-fit:cover}
.blob .monogram{font-size:clamp(5rem,13vw,9.5rem);color:var(--accent)}
@keyframes breathe{0%{border-radius:63% 37% 54% 46%/55% 48% 52% 45%}50%{border-radius:40% 60% 70% 30%/42% 50% 60% 58%}100%{border-radius:70% 30% 46% 54%/32% 38% 62% 68%}}
.lay-flow main>section{padding-block:clamp(3.5rem,8vw,6.5rem)}
.lay-flow h2{font-size:clamp(2rem,3.8vw,3.1rem);margin-bottom:1.25rem}
.lay-flow h3{font-size:1.45rem;margin-bottom:.6rem}
.f-about{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);gap:clamp(1.5rem,5vw,5rem)}
.f-about .text{max-width:60ch}.f-about .text p:first-child{font-size:1.2rem;line-height:1.6}
.f-intro{max-width:52ch;color:var(--muted);font-size:1.12rem;margin-bottom:2.5rem}
.pebbles{display:flex;flex-wrap:wrap;gap:1.25rem;list-style:none}
.pebbles li{flex:1 1 15rem;background:var(--soft);padding:2.1rem 2.1rem 2.4rem;border-radius:3rem 1.25rem 3.5rem 1.6rem/2.6rem 1.8rem 3rem 1.25rem}
.pebbles li:nth-child(3n+2){border-radius:1.4rem 3.6rem 1.6rem 3rem/2rem 2.6rem 1.4rem 3.2rem;flex-basis:19rem}
.pebbles li:nth-child(3n){border-radius:2.6rem 2rem 1.3rem 3.8rem/1.6rem 3.4rem 2.4rem 2rem;background:color-mix(in srgb,var(--soft) 55%,var(--bg))}
.pebbles p{margin:0;color:color-mix(in srgb,var(--ink) 85%,var(--soft))}
.grove{background:color-mix(in srgb,var(--accent) 11%,#fff);border-radius:4.5rem 9rem 5rem 7rem/6rem 5rem 8rem 4rem;padding:clamp(2rem,6vw,5rem)}
.grove ul{list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:2.5rem 3.5rem;margin-top:2rem}
.grove .detail{display:block;margin-top:.75rem;font-style:italic;color:var(--accent)}
.path{list-style:none;counter-reset:step;display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:2.5rem;margin-top:2.5rem}
.path li{counter-increment:step}
.path li::before{content:counter(step);display:grid;place-items:center;width:3.4rem;height:3.4rem;margin-bottom:1.1rem;background:var(--accent);color:var(--accent-ink);font-family:var(--display);font-size:1.35rem;border-radius:55% 45% 52% 48%/46% 56% 44% 54%}
.path p{color:var(--muted)}
.f-faq .list{max-width:50rem}
.f-faq details{background:color-mix(in srgb,var(--soft) 55%,var(--bg));border-radius:1.75rem 1.1rem 1.75rem 1.1rem;margin-bottom:.75rem}
.f-faq summary{display:flex;justify-content:space-between;align-items:center;gap:1.5rem;padding:1.15rem 1.6rem;font-weight:600}
.f-faq summary::after{content:"+";font-family:var(--display);font-size:1.6rem;line-height:1;color:var(--accent);transition:transform .25s}
.f-faq details[open] summary::after{transform:rotate(45deg)}
.f-faq .answer{padding:0 1.6rem 1.4rem;max-width:62ch}
.pond{--btn-bg:var(--accent-ink);--btn-fg:var(--accent);background:var(--accent);color:var(--accent-ink);border-radius:5rem 3rem 6.5rem 2.5rem/4rem 6rem 3rem 5.5rem;padding:clamp(2.25rem,6vw,5rem);display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:2.5rem 4rem;align-items:start}
.pond h2{margin-bottom:1rem}.pond .lede{font-size:1.15rem;max-width:36ch;margin-bottom:2rem}
.pond dl div{padding-block:.7rem;border-bottom:1px solid color-mix(in srgb,var(--accent-ink) 25%,transparent)}
.pond dt{font-size:.85rem;opacity:.75}.pond dd{font-size:1.05rem}
.lay-flow .emergency{max-width:62ch;margin:2rem auto 0;text-align:center;font-size:.95rem;color:var(--muted)}
.lay-flow .emergency strong{display:block;color:var(--ink);margin-bottom:.25rem}
.wave{display:block;width:100%;height:clamp(2.5rem,6vw,5rem);color:var(--soft);margin-top:clamp(2rem,6vw,4rem)}
.f-foot{background:var(--soft);padding-block:1rem 3rem;font-size:.95rem}
.f-foot .wrap{display:flex;flex-wrap:wrap;justify-content:space-between;gap:1rem 2rem}
.f-foot .name{font-family:var(--display);font-size:1.2rem}
.f-foot .links{display:flex;gap:1.5rem}
@media (max-width:52rem){.f-hero,.f-about,.pond{grid-template-columns:1fr}.stage{width:min(80%,22rem);grid-row:1}}
"""


def flow(p: Page) -> str:
    c, i = p.c, p.i
    hero = f"""
<div class="wrap">
  <header class="top"><a class="brand" href="#top">{e(i.get('practice_name'))}</a>{p.nav()}</header>
  <section class="f-hero" id="top">
    <div>
      <h1>{e(c.get('hero_headline'))}</h1>
      <p class="sub">{e(c.get('hero_subhead'))}</p>
      {p.btn()}
      <p class="who">{p.who()}</p>
    </div>
    <div class="stage"><div class="blob back"></div><div class="blob front">{p.portrait()}</div></div>
  </section>
</div>"""

    blocks = {
        "about": f"""<section id="about"><div class="wrap f-about">
  <h2>{e(c.get('about_title'))}</h2><div class="text">{paras(c.get('about_body'))}</div></div></section>""",
        "approach": f"""<section id="approach"><div class="wrap">
  <h2>{e(c.get('approach_title'))}</h2><p class="f-intro">{e(c.get('approach_intro'))}</p>
  <ul class="pebbles">{''.join(f"<li><h3>{e(a.get('title'))}</h3><p>{e(a.get('text'))}</p></li>" for a in c.get('approaches', []))}</ul>
</div></section>""",
        "services": f"""<section id="services"><div class="wrap"><div class="grove">
  <h2>{e(c.get('services_title'))}</h2>
  <ul>{''.join(f"<li><h3>{e(s.get('title'))}</h3><p>{e(s.get('text'))}</p>" + (f"<span class='detail'>{e(s.get('detail'))}</span>" if s.get('detail') else '') + "</li>" for s in c.get('services', []))}</ul>
</div></div></section>""",
        "process": f"""<section id="process"><div class="wrap">
  <h2>{e(c.get('process_title'))}</h2>
  <ol class="path">{''.join(f"<li><h3>{e(s.get('title'))}</h3><p>{e(s.get('text'))}</p></li>" for s in c.get('steps', []))}</ol>
</div></section>""",
        "faq": f"""<section id="faq"><div class="wrap f-faq"><h2>{e(c.get('faq_title'))}</h2><div class="list">{p.faqs()}</div></div></section>""",
        "contact": f"""<section id="contact"><div class="wrap">
  <div class="pond"><div><h2>{e(c.get('contact_title'))}</h2><p class="lede">{e(c.get('contact_body'))}</p>{p.btn()}</div>{p.contact_dl()}</div>
  {p.emergency()}
</div></section>""",
    }
    foot = f"""
<svg class="wave" viewBox="0 0 1440 80" preserveAspectRatio="none" aria-hidden="true"><path fill="currentColor" d="M0 44C180 78 360 6 620 28S1080 74 1260 40 1440 22 1440 22V80H0Z"/></svg>
<footer class="f-foot"><div class="wrap"><span class="name">{e(i.get('practice_name'))}</span><span>{e(i.get('address'))}</span><span class="links">{p.legal_links()}</span></div></footer>"""
    return hero + "<main id=\"main\">" + "".join(blocks[s] for s in p.order) + "</main>" + foot


# --------------------------------------------------------------------------
# Clinical grid: ruled 12-column grid, intake-card hero, tabular services.
# --------------------------------------------------------------------------

GRID_CSS = """
.lay-grid{font-size:1rem;line-height:1.6}
.lay-grid .wrap{max-width:82rem}
.g-top{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:.75rem 2rem;padding-block:1.15rem;border-bottom:2px solid var(--ink)}
.g-top .brand{font-weight:700;font-size:1.05rem;text-decoration:none;letter-spacing:-.01em}
.g-top ul{display:flex;flex-wrap:wrap;gap:.25rem 1.6rem;list-style:none;font-size:.94rem}
.g-top a{text-decoration:none}.g-top nav a:hover{text-decoration:underline}
.g-row{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));border-bottom:1px solid var(--ink)}
.g-lead{grid-column:1/span 8;padding:clamp(2.5rem,6vw,5rem) clamp(1.25rem,3vw,3rem) clamp(2.5rem,5vw,4rem) 0;border-right:1px solid var(--line);display:flex;flex-direction:column;justify-content:space-between;gap:2.5rem}
.g-lead h1{font-size:clamp(2.7rem,6.6vw,5.9rem);line-height:.97}
.g-lead .sub{font-size:1.22rem;line-height:1.5;max-width:40ch;margin:1.8rem 0 2.25rem;color:var(--muted)}
.g-sheet{grid-column:9/span 4;display:flex;flex-direction:column}
.g-sheet .photo,.g-sheet .monogram{aspect-ratio:4/5;width:100%;height:auto;object-fit:cover;border-bottom:1px solid var(--line);filter:grayscale(1) contrast(1.04)}
.g-sheet .monogram{background:var(--soft);font-size:clamp(4rem,9vw,7.5rem);font-weight:300;letter-spacing:-.05em}
.g-sheet dl div,.g-dl div{display:grid;grid-template-columns:7.5rem minmax(0,1fr);gap:1rem;padding:.8rem 0 .8rem 1.25rem;border-bottom:1px solid var(--line)}
.g-sheet dl div:last-child{border-bottom:0}
.g-sheet dt,.g-dl dt{color:var(--muted);font-size:.86rem;padding-top:.1em}.g-sheet dd{font-size:.95rem}
.g-label{grid-column:1/span 3;padding:2.75rem 1.5rem 2.75rem 0;border-right:1px solid var(--line)}
.g-label h2{font-size:clamp(1.45rem,2.3vw,2rem);line-height:1.1;position:sticky;top:1.5rem}
.g-body{grid-column:4/span 9;padding:2.75rem 0 3.25rem clamp(1.25rem,3vw,2.5rem);min-width:0}
.g-body .measure{max-width:64ch}.g-about p:first-child{font-size:1.36rem;line-height:1.45;letter-spacing:-.01em}
.g-intro{max-width:56ch;color:var(--muted);margin-bottom:2rem}
.g-cells{display:grid;grid-template-columns:repeat(auto-fill,minmax(15rem,1fr));border-top:1px solid var(--line);border-left:1px solid var(--line);list-style:none}
.g-cells li{padding:1.4rem 1.5rem 1.7rem;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.g-cells h3,.g-svc h3,.g-steps h3{font-size:1.08rem;font-weight:650;letter-spacing:-.01em;margin-bottom:.45rem;font-family:var(--body)}
.g-cells p{color:var(--muted);font-size:.96rem}
.g-svc{list-style:none;border-top:1px solid var(--ink)}
.g-svc li{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.6fr) minmax(9rem,.9fr);gap:1.5rem;padding:1.25rem 0;border-bottom:1px solid var(--line)}
.g-svc p{color:var(--muted)}.g-svc .detail{text-align:right;font-variant-numeric:tabular-nums;font-size:.95rem}
.g-steps{list-style:none;counter-reset:step;display:grid;grid-template-columns:repeat(auto-fit,minmax(12rem,1fr));border-left:1px solid var(--line)}
.g-steps li{counter-increment:step;padding:0 1.4rem 1rem;border-right:1px solid var(--line)}
.g-steps li::before{content:counter(step);display:block;font-size:3.4rem;font-weight:300;line-height:1;letter-spacing:-.04em;margin-bottom:1.4rem;font-variant-numeric:tabular-nums}
.g-steps p{color:var(--muted);font-size:.96rem}
.g-faq details{border-bottom:1px solid var(--line)}.g-faq details:first-child{border-top:1px solid var(--ink)}
.g-faq summary{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2rem;padding:1.1rem 0;font-weight:600}
.g-faq summary::after{content:"+";font-weight:400;font-size:1.3rem;line-height:1}.g-faq details[open] summary::after{content:"\\2212"}
.g-faq .answer{padding:0 3rem 1.4rem 0;max-width:64ch;color:var(--muted)}
.g-contact{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:2.5rem}
.g-contact .lede{font-size:1.2rem;max-width:36ch;margin-bottom:1.75rem}
.g-dl{border-top:1px solid var(--ink)}.g-dl div{padding-left:0}
.lay-grid .emergency{display:grid;grid-template-columns:9rem minmax(0,1fr);gap:1rem;border:2px solid var(--ink);padding:1.15rem 1.4rem;margin-block:2.5rem}
.lay-grid .emergency p{max-width:70ch}
.g-foot{display:flex;flex-wrap:wrap;gap:.5rem 2rem;justify-content:space-between;padding-block:1.4rem 2.5rem;font-size:.9rem;color:var(--muted)}
.g-foot .links{display:flex;gap:1.5rem}
@media (max-width:56rem){
 .g-lead,.g-sheet,.g-label,.g-body{grid-column:1/-1;border-right:0;padding-left:0;padding-right:0}
 .g-sheet{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);border-top:1px solid var(--line)}
 .g-sheet .photo,.g-sheet .monogram{border-bottom:0;border-right:1px solid var(--line);height:100%}
 .g-label{padding-bottom:0}.g-label h2{position:static}.g-body{padding-top:1.25rem}
 .g-svc li,.g-contact{grid-template-columns:1fr;gap:.4rem}.g-svc .detail{text-align:left}
 .lay-grid .emergency{grid-template-columns:1fr}
}
@media (max-width:30rem){.g-sheet{grid-template-columns:1fr}.g-sheet .photo,.g-sheet .monogram{border-right:0;border-bottom:1px solid var(--line)}}
"""


def grid(p: Page) -> str:
    c, i = p.c, p.i
    facts = "".join(f"<div><dt>{e(k)}</dt><dd>{v}</dd></div>" for k, v in p.facts())

    def row(sid: str, title: str, body: str, cls: str = "") -> str:
        return (
            f'<section class="g-row" id="{sid}"><div class="g-label"><h2>{e(title)}</h2></div>'
            f'<div class="g-body {cls}">{body}</div></section>'
        )

    head = f"""
<div class="wrap">
<header class="g-top"><a class="brand" href="#top">{e(i.get('practice_name'))}</a>{p.nav()}</header>
<section class="g-row" id="top">
  <div class="g-lead"><div><h1>{e(c.get('hero_headline'))}</h1><p class="sub">{e(c.get('hero_subhead'))}</p></div><div>{p.btn()}</div></div>
  <aside class="g-sheet">{p.portrait()}<dl>{facts}</dl></aside>
</section>"""

    blocks = {
        "about": row("about", c.get("about_title"), f'<div class="measure g-about">{paras(c.get("about_body"))}</div>'),
        "approach": row(
            "approach", c.get("approach_title"),
            f'<p class="g-intro">{e(c.get("approach_intro"))}</p><ul class="g-cells">'
            + "".join(f"<li><h3>{e(a.get('title'))}</h3><p>{e(a.get('text'))}</p></li>" for a in c.get("approaches", []))
            + "</ul>",
        ),
        "services": row(
            "services", c.get("services_title"),
            '<ul class="g-svc">'
            + "".join(
                f"<li><h3>{e(s.get('title'))}</h3><p>{e(s.get('text'))}</p><span class='detail'>{e(s.get('detail'))}</span></li>"
                for s in c.get("services", [])
            )
            + "</ul>",
        ),
        "process": row(
            "process", c.get("process_title"),
            '<ol class="g-steps">'
            + "".join(f"<li><h3>{e(s.get('title'))}</h3><p>{e(s.get('text'))}</p></li>" for s in c.get("steps", []))
            + "</ol>",
        ),
        "faq": row("faq", c.get("faq_title"), f'<div class="g-faq">{p.faqs()}</div>'),
        "contact": row(
            "contact", c.get("contact_title"),
            f'<div class="g-contact"><div><p class="lede">{e(c.get("contact_body"))}</p>{p.btn()}</div>'
            f'{p.contact_dl("g-dl")}</div>{p.emergency()}',
        ),
    }
    where = ", ".join(e(x) for x in (i.get("practice_name"), i.get("address")) if x)
    foot = f"""<footer class="g-foot"><span>{where}</span><span class="links">{p.legal_links()}</span><span>{p.year()}</span></footer></div>"""
    return head + '<main id="main">' + "".join(blocks[s] for s in p.order) + "</main>" + foot


# --------------------------------------------------------------------------
# Luxury cinema: letterboxed opening titles, framed portrait, a menu of services.
# --------------------------------------------------------------------------

CINEMA_CSS = """
.lay-cinema{font-weight:350;letter-spacing:.005em}
.lay-cinema .btn{background:transparent;color:var(--accent);border-width:1px;font-weight:400;letter-spacing:.06em;padding:1em 2.5em}
.lay-cinema .btn:hover{background:var(--accent);color:var(--accent-ink)}
.k-hero{--bar:clamp(3rem,9vh,5.5rem);position:relative;min-height:min(100svh,62rem);display:grid;place-items:center;text-align:center;padding:calc(var(--bar) + 4rem) 1.25rem calc(var(--bar) + 3.5rem);overflow:hidden;
 background:radial-gradient(110% 85% at 50% 42%,color-mix(in srgb,var(--soft) 92%,var(--ink)) 0%,var(--bg) 58%,color-mix(in srgb,var(--bg) 72%,#000) 100%)}
.k-hero::before,.k-hero::after{content:"";position:absolute;left:0;right:0;height:var(--bar);background:color-mix(in srgb,var(--bg) 30%,#000);z-index:1;animation:bars 1.5s cubic-bezier(.65,0,.2,1) both}
.k-hero::before{top:0;transform-origin:top}.k-hero::after{bottom:0;transform-origin:bottom}
@keyframes bars{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.k-frame{position:absolute;inset:calc(var(--bar) + 1.25rem) clamp(1rem,3vw,2.25rem);border:1px solid color-mix(in srgb,var(--accent) 50%,transparent);pointer-events:none}
.k-top{position:absolute;top:0;left:0;right:0;height:var(--bar);z-index:3;display:flex;align-items:center;justify-content:space-between;gap:2rem;padding-inline:clamp(1.25rem,4vw,3rem);animation:fade 1s .6s both}
.k-top .brand{font-family:var(--display);font-style:italic;font-size:1.2rem;text-decoration:none;color:var(--ink);white-space:nowrap}
.k-top ul{display:flex;gap:1.75rem;list-style:none;font-size:.88rem;letter-spacing:.06em;overflow-x:auto;white-space:nowrap;scrollbar-width:none}
.k-top a{text-decoration:none;color:var(--muted)}.k-top nav a:hover{color:var(--accent)}
.k-titles{position:relative;z-index:2;max-width:58rem;animation:rise 1.5s 1s ease-out both}
@keyframes rise{from{opacity:0;transform:translateY(1rem)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
.k-credit{font-family:var(--display);font-style:italic;font-size:1.15rem;color:var(--accent);margin-bottom:1.8rem}
.k-titles h1{font-size:clamp(2.8rem,7.2vw,6.25rem);line-height:1.02}
.k-titles .sub{font-size:1.15rem;font-weight:300;line-height:1.7;max-width:40ch;margin:2rem auto 2.75rem;color:var(--muted)}
.lay-cinema main>section{padding-block:clamp(4.5rem,10vw,8.5rem)}
.lay-cinema h2{font-size:clamp(2.2rem,4.6vw,3.7rem);font-style:italic;line-height:1.08;margin-bottom:1.5rem}
.lay-cinema h3{font-size:1.65rem;margin-bottom:.6rem}
.k-about{display:grid;grid-template-columns:minmax(0,.85fr) minmax(0,1.15fr);gap:clamp(2.5rem,7vw,7rem);align-items:center}
.k-portrait{position:relative;max-width:26rem;width:100%}
.k-portrait::before{content:"";position:absolute;inset:1.1rem -1.1rem -1.1rem 1.1rem;border:1px solid var(--accent)}
.k-portrait .photo,.k-portrait .monogram{position:relative;aspect-ratio:4/5;width:100%;height:auto;object-fit:cover;filter:saturate(.8) contrast(1.05)}
.k-portrait .monogram{background:var(--soft);color:var(--accent);font-style:italic;font-size:clamp(5rem,12vw,8rem)}
.k-about .text{max-width:56ch;font-size:1.06rem;line-height:1.8}
.k-center{text-align:center;max-width:48rem;margin-inline:auto}
.k-intro{color:var(--muted);max-width:50ch;margin:0 auto 3rem;font-size:1.1rem}
.k-list{list-style:none}.k-list li{max-width:44ch;margin-inline:auto}.k-list p{color:var(--muted)}
.k-list li+li::before{content:"";display:block;width:3rem;height:1px;background:var(--accent);margin:2.75rem auto}
.k-menu{list-style:none;max-width:48rem;margin:3rem auto 0}
.k-menu li{padding-block:1.4rem;border-top:1px solid color-mix(in srgb,var(--accent) 22%,transparent)}
.k-menu .row{display:flex;align-items:baseline;gap:1rem}
.k-menu h3{margin:0;font-size:1.55rem}
.k-menu .lead{flex:1;min-width:2rem;border-bottom:1px dotted color-mix(in srgb,var(--accent) 60%,transparent);transform:translateY(-.3em)}
.k-menu .detail{color:var(--accent);font-size:.95rem;letter-spacing:.03em;text-align:right;max-width:45%}
.k-menu p{color:var(--muted);margin-top:.5rem;max-width:56ch}
.k-steps{list-style:none;counter-reset:step;display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:3rem 2.5rem;margin-top:3.25rem;text-align:center}
.k-steps li{counter-increment:step}
.k-steps li::before{content:counter(step,upper-roman);display:block;font-family:var(--display);font-style:italic;font-size:2.3rem;color:var(--accent);margin-bottom:1rem}
.k-steps h3{font-size:1.4rem}.k-steps p{color:var(--muted);max-width:30ch;margin-inline:auto}
.k-faq{max-width:46rem;margin:2.5rem auto 0;text-align:left}
.k-faq details{border-top:1px solid color-mix(in srgb,var(--accent) 30%,transparent)}.k-faq details:last-child{border-bottom:1px solid color-mix(in srgb,var(--accent) 30%,transparent)}
.k-faq summary{display:flex;justify-content:space-between;gap:2rem;padding:1.35rem 0;font-family:var(--display);font-size:1.3rem}
.k-faq summary::after{content:"+";color:var(--accent);font-family:var(--body);font-weight:300;transition:transform .3s}
.k-faq details[open] summary::after{transform:rotate(45deg)}
.k-faq .answer{padding-bottom:1.5rem;color:var(--muted);max-width:60ch}
.lay-cinema .k-contact{background:color-mix(in srgb,var(--bg) 62%,#000);text-align:center}
.k-contact .lede{max-width:44ch;margin:0 auto 2.75rem;color:var(--muted);font-size:1.1rem}
.k-contact dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(12rem,1fr));gap:2rem;max-width:56rem;margin:0 auto 3rem}
.k-contact dt{font-family:var(--display);font-style:italic;color:var(--accent);margin-bottom:.35rem}
.lay-cinema .emergency{max-width:52ch;margin:4rem auto 0;padding-top:2rem;border-top:1px solid color-mix(in srgb,var(--accent) 35%,transparent);font-size:.94rem;color:var(--muted)}
.lay-cinema .emergency strong{display:block;font-weight:500;color:var(--ink);margin-bottom:.35rem}
.k-foot{text-align:center;padding:3rem 1.25rem 3.5rem;font-size:.88rem;color:var(--muted);background:color-mix(in srgb,var(--bg) 62%,#000);border-top:1px solid color-mix(in srgb,var(--accent) 18%,transparent)}
.k-foot .name{display:block;font-family:var(--display);font-style:italic;font-size:1.35rem;color:var(--ink);margin-bottom:.5rem}
.k-foot .links{display:flex;justify-content:center;gap:1.75rem;margin-top:.9rem}
@media (max-width:52rem){.k-about{grid-template-columns:1fr}.k-portrait{margin-inline:auto;width:80%}.k-top nav{display:none}.k-top{justify-content:center}}
"""


def cinema(p: Page) -> str:
    c, i = p.c, p.i
    hero = f"""
<section class="k-hero" id="top">
  <header class="k-top"><a class="brand" href="#top">{e(i.get('practice_name'))}</a>{p.nav()}</header>
  <div class="k-frame" aria-hidden="true"></div>
  <div class="k-titles">
    <p class="k-credit">{p.who()}</p>
    <h1>{e(c.get('hero_headline'))}</h1>
    <p class="sub">{e(c.get('hero_subhead'))}</p>
    {p.btn()}
  </div>
</section>"""

    def menu_item(s: dict) -> str:
        detail = f"<span class='lead'></span><span class='detail'>{e(s.get('detail'))}</span>" if s.get("detail") else ""
        return f"<li><div class='row'><h3>{e(s.get('title'))}</h3>{detail}</div><p>{e(s.get('text'))}</p></li>"

    blocks = {
        "about": f"""<section id="about"><div class="wrap k-about">
  <figure class="k-portrait" style="margin:0">{p.portrait()}</figure>
  <div><h2>{e(c.get('about_title'))}</h2><div class="text">{paras(c.get('about_body'))}</div></div></div></section>""",
        "approach": f"""<section id="approach"><div class="wrap k-center">
  <h2>{e(c.get('approach_title'))}</h2><p class="k-intro">{e(c.get('approach_intro'))}</p>
  <ul class="k-list">{''.join(f"<li><h3>{e(a.get('title'))}</h3><p>{e(a.get('text'))}</p></li>" for a in c.get('approaches', []))}</ul>
</div></section>""",
        "services": f"""<section id="services"><div class="wrap"><h2 class="k-center">{e(c.get('services_title'))}</h2>
  <ul class="k-menu">{''.join(menu_item(s) for s in c.get('services', []))}</ul></div></section>""",
        "process": f"""<section id="process"><div class="wrap"><h2 class="k-center">{e(c.get('process_title'))}</h2>
  <ol class="k-steps">{''.join(f"<li><h3>{e(s.get('title'))}</h3><p>{e(s.get('text'))}</p></li>" for s in c.get('steps', []))}</ol></div></section>""",
        "faq": f"""<section id="faq"><div class="wrap"><h2 class="k-center">{e(c.get('faq_title'))}</h2><div class="k-faq">{p.faqs()}</div></div></section>""",
        "contact": f"""<section id="contact" class="k-contact"><div class="wrap">
  <h2>{e(c.get('contact_title'))}</h2><p class="lede">{e(c.get('contact_body'))}</p>
  {p.contact_dl()}{p.btn()}{p.emergency()}
</div></section>""",
    }
    foot = f"""<footer class="k-foot"><span class="name">{e(i.get('practice_name'))}</span>{e(i.get('address'))}<div class="links">{p.legal_links()}</div></footer>"""
    return hero + '<main id="main">' + "".join(blocks[s] for s in p.order) + "</main>" + foot


# --------------------------------------------------------------------------
# Bold diagonal: split hero, slanted colour bands, outlined step numerals.
# --------------------------------------------------------------------------

DIAGONAL_CSS = """
.lay-diagonal{--slant:3.5vw}
.d-hero{position:relative;background:var(--accent);color:var(--accent-ink);overflow:hidden}
.d-panel{position:absolute;inset:0;background:var(--ink);clip-path:polygon(0 0,70% 0,53% 100%,0 100%);animation:slice 1s cubic-bezier(.7,0,.2,1) both}
@keyframes slice{from{clip-path:polygon(0 0,0 0,0 100%,0 100%)}}
.d-bar{position:relative;z-index:2;background:var(--ink);color:var(--bg)}
.d-top{display:flex;justify-content:space-between;align-items:center;gap:1rem 2rem;flex-wrap:wrap;padding-block:1.4rem}
.d-top .brand{font-weight:800;font-stretch:125%;font-size:1.15rem;text-decoration:none;letter-spacing:-.01em}
.d-top ul{display:flex;flex-wrap:wrap;gap:.3rem 1.5rem;list-style:none;font-weight:600;font-size:.95rem}
.d-top nav a{text-decoration:none}.d-top nav a:hover{text-decoration:underline;text-decoration-thickness:2px}
.d-inner{position:relative;z-index:1;display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);align-items:end;min-height:min(84svh,48rem)}
.d-copy{color:var(--bg);padding-block:clamp(2.5rem,8vh,5rem) clamp(3.5rem,10vh,6rem);align-self:center}
.d-copy h1{font-size:clamp(2.6rem,6.3vw,5.9rem);line-height:.93}
.d-copy .sub{font-size:1.2rem;line-height:1.55;max-width:32ch;margin:1.8rem 0 2.4rem;color:color-mix(in srgb,var(--bg) 82%,var(--ink))}
.d-art{justify-self:end;width:min(100%,27rem);aspect-ratio:3/4}
.d-art .photo{width:100%;height:100%;object-fit:cover;clip-path:polygon(22% 0,100% 0,100% 100%,0 100%)}
.d-art .monogram{font-weight:900;font-stretch:125%;font-size:clamp(7rem,19vw,15rem);letter-spacing:-.06em;color:var(--ink);align-items:end;justify-items:end;padding-bottom:.1em}
.lay-diagonal main>section{position:relative;padding-block:clamp(4.5rem,10vw,8rem)}
.lay-diagonal main>section+section,.d-hero+main>section:first-child{clip-path:polygon(0 var(--slant),100% 0,100% 100%,0 100%);margin-top:calc(var(--slant) * -1);padding-top:calc(clamp(4.5rem,10vw,8rem) + var(--slant))}
.band-tint{background:var(--soft);--fg:var(--ink)}.band-plain{background:var(--bg);--fg:var(--ink)}
.band-dark{background:var(--ink);color:var(--bg);--fg:var(--bg)}
.lay-diagonal h2{font-size:clamp(2.4rem,5.6vw,4.9rem);line-height:.95;max-width:16ch;margin-bottom:2.75rem}
.lay-diagonal h3{font-size:1.35rem;font-weight:800;font-stretch:112%;margin-bottom:.5rem}
.d-about{max-width:46rem}
.d-about p:first-child{font-size:clamp(1.3rem,2.2vw,1.65rem);line-height:1.4;font-weight:500;margin-bottom:1.25em}
.d-intro{font-size:1.2rem;max-width:44ch;margin:-1rem 0 2.5rem}
.d-stack{list-style:none}
.d-stack li{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:.5rem 3rem;padding-block:1.8rem;border-top:4px solid currentColor}
.d-stack h3{font-size:clamp(1.7rem,3.4vw,2.7rem);font-weight:850;font-stretch:125%;line-height:1;margin:0}
.d-stack p{max-width:50ch}
.d-svc{list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:2.5rem 2rem}
.d-svc li{border-left:5px solid var(--accent);padding:0 0 .25rem 1.4rem}
.d-svc .detail{display:inline-block;margin-top:1rem;padding:.25em .7em;background:var(--accent);color:var(--accent-ink);font-weight:700;font-size:.9rem;transform:skewX(-10deg)}
.d-steps{list-style:none;counter-reset:step;display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:2.5rem}
.d-steps li{counter-increment:step}
.d-steps li::before{content:counter(step);display:block;font-family:var(--display);font-weight:900;font-stretch:125%;font-size:clamp(4.5rem,8vw,6.5rem);line-height:.9;color:transparent;-webkit-text-stroke:2px var(--fg,var(--ink));margin-bottom:.75rem}
.d-faq details{max-width:58rem}
.d-faq details{border-top:4px solid currentColor}.d-faq details:last-child{border-bottom:4px solid currentColor}
.d-faq summary{display:flex;justify-content:space-between;align-items:center;gap:2rem;padding:1.25rem 0;font-size:1.2rem;font-weight:700}
.d-faq summary::after{content:"+";flex:none;display:grid;place-items:center;width:2.2rem;height:2.2rem;background:var(--accent);color:var(--accent-ink);font-size:1.5rem;font-weight:800;transition:transform .25s}
.d-faq details[open] summary::after{transform:rotate(45deg)}
.d-faq .answer{padding-bottom:1.5rem;max-width:62ch}
.lay-diagonal main>section.d-contact{background:var(--accent);color:var(--accent-ink);--btn-bg:var(--ink);--btn-fg:var(--bg)}
.d-contact::before{content:"";position:absolute;inset:0;background:var(--ink);clip-path:polygon(56% 0,100% 0,100% 100%,40% 100%)}
.d-contact .wrap{position:relative;display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,.75fr);gap:3rem 5rem;align-items:center}
.d-contact .lede{font-size:1.25rem;max-width:24ch;margin-bottom:2.25rem}
.d-contact dl{color:var(--bg)}
.d-contact dl div{padding-block:.8rem;border-bottom:2px solid color-mix(in srgb,var(--bg) 25%,transparent)}
.d-contact dt{font-weight:700;font-size:.88rem;color:var(--accent)}
.d-emergency{background:var(--soft);color:var(--ink);padding-block:1.75rem}
.d-emergency .emergency{display:grid;grid-template-columns:auto minmax(0,1fr);gap:.5rem 1.5rem;align-items:baseline}
.d-emergency strong{font-stretch:112%;font-weight:800}
.d-foot{background:var(--ink);color:var(--bg);padding-block:2rem 2.5rem;font-size:.92rem}
.d-foot .wrap{display:flex;flex-wrap:wrap;justify-content:space-between;gap:1rem 2rem}
.d-foot .name{font-weight:800;font-stretch:125%}
.d-foot .links{display:flex;gap:1.5rem}
@media (max-width:52rem){
 .d-hero{background:var(--ink)}.d-panel{display:none}
 .d-inner{grid-template-columns:1fr;min-height:0}
 .d-copy{padding-bottom:3rem}
 .d-art{justify-self:stretch;width:auto;aspect-ratio:auto;height:15rem;margin-inline:calc(-1*clamp(1.125rem,4vw,2.5rem));background:var(--accent);clip-path:polygon(0 22%,100% 0,100% 100%,0 100%)}
 .d-art .photo{clip-path:none}
 .d-stack li,.d-contact .wrap{grid-template-columns:1fr}
 .d-contact::before{display:none}
 .d-contact dl{background:var(--ink);padding:2.5rem 1.5rem 1.5rem;clip-path:polygon(0 1.25rem,100% 0,100% 100%,0 100%)}
 .d-emergency .emergency{grid-template-columns:1fr}
}
"""


def diagonal(p: Page) -> str:
    c, i = p.c, p.i
    hero = f"""
<section class="d-hero" id="top">
  <div class="d-bar"><header class="wrap d-top"><a class="brand" href="#top">{e(i.get('practice_name'))}</a>{p.nav()}</header></div>
  <div class="d-panel" aria-hidden="true"></div>
  <div class="wrap">
    <div class="d-inner">
      <div class="d-copy"><h1>{e(c.get('hero_headline'))}</h1><p class="sub">{e(c.get('hero_subhead'))}</p>{p.btn()}</div>
      <div class="d-art">{p.portrait()}</div>
    </div>
  </div>
</section>"""

    bands = ["band-tint", "band-dark", "band-plain"]
    band_of = {}
    n = 0
    for s in p.order:
        if s != "contact":
            band_of[s] = bands[n % 3]
            n += 1

    blocks = {
        "about": lambda b: f"""<section id="about" class="{b}"><div class="wrap"><h2>{e(c.get('about_title'))}</h2><div class="d-about">{paras(c.get('about_body'))}</div></div></section>""",
        "approach": lambda b: f"""<section id="approach" class="{b}"><div class="wrap">
  <h2>{e(c.get('approach_title'))}</h2><p class="d-intro">{e(c.get('approach_intro'))}</p>
  <ul class="d-stack">{''.join(f"<li><h3>{e(a.get('title'))}</h3><p>{e(a.get('text'))}</p></li>" for a in c.get('approaches', []))}</ul></div></section>""",
        "services": lambda b: f"""<section id="services" class="{b}"><div class="wrap"><h2>{e(c.get('services_title'))}</h2>
  <ul class="d-svc">{''.join(f"<li><h3>{e(s.get('title'))}</h3><p>{e(s.get('text'))}</p>" + (f"<span class='detail'>{e(s.get('detail'))}</span>" if s.get('detail') else '') + "</li>" for s in c.get('services', []))}</ul></div></section>""",
        "process": lambda b: f"""<section id="process" class="{b}"><div class="wrap"><h2>{e(c.get('process_title'))}</h2>
  <ol class="d-steps">{''.join(f"<li><h3>{e(s.get('title'))}</h3><p>{e(s.get('text'))}</p></li>" for s in c.get('steps', []))}</ol></div></section>""",
        "faq": lambda b: f"""<section id="faq" class="{b}"><div class="wrap d-faq"><h2>{e(c.get('faq_title'))}</h2>{p.faqs()}</div></section>""",
        "contact": lambda b: f"""<section id="contact" class="d-contact"><div class="wrap">
  <div><h2>{e(c.get('contact_title'))}</h2><p class="lede">{e(c.get('contact_body'))}</p>{p.btn()}</div>{p.contact_dl()}</div></section>""",
    }
    emergency = p.emergency()
    tail = f'<div class="d-emergency"><div class="wrap">{emergency}</div></div>' if emergency else ""
    foot = f"""{tail}<footer class="d-foot"><div class="wrap"><span class="name">{e(i.get('practice_name'))}</span><span>{e(i.get('address'))}</span><span class="links">{p.legal_links()}</span></div></footer>"""
    return hero + '<main id="main">' + "".join(blocks[s](band_of.get(s, "")) for s in p.order) + "</main>" + foot


LAYOUT_RENDERERS = {
    "flow": (flow, FLOW_CSS),
    "grid": (grid, GRID_CSS),
    "cinema": (cinema, CINEMA_CSS),
    "diagonal": (diagonal, DIAGONAL_CSS),
}


def render_page(
    copy: dict,
    intake: dict,
    theme_key: str,
    *,
    layout: str | None = None,
    colors: dict | None = None,
    button_shape: str | None = None,
    order: list[str] | None = None,
) -> str:
    theme = THEMES[theme_key]
    layout = layout if layout in LAYOUT_RENDERERS else theme.layout
    shape = button_shape if button_shape in BUTTON_SHAPES else theme.button_shape

    palette = {"bg": theme.bg, "soft": theme.soft, "ink": theme.ink, "accent": theme.accent}
    for k, v in (colors or {}).items():
        if k in palette and isinstance(v, str) and HEX.match(v):
            palette[k] = v
    accent_ink = theme.accent_ink if palette["accent"] == theme.accent else readable_on(palette["accent"])

    tokens = (
        f":root{{--bg:{palette['bg']};--soft:{palette['soft']};--ink:{palette['ink']};"
        f"--accent:{palette['accent']};--accent-ink:{accent_ink};"
        f"--display:{theme.display_font};--body:{theme.body_font};{theme.extra}}}"
    )
    renderer, layout_css = LAYOUT_RENDERERS[layout]
    page = Page(copy, intake, order or list(SECTIONS))
    body = renderer(page).replace('class="btn ', f'class="btn shape-{shape} ')

    lang = page.lang
    title = " – ".join(x for x in (intake.get("practice_name"), intake.get("city")) if x)
    return f"""<!doctype html>
<html lang="{e(lang)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(copy.get('meta_description'))}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{e(theme.fonts_url)}">
<style>{tokens}{BASE_CSS}{layout_css}</style>
</head>
<body class="lay-{layout}">
<a class="skip" href="#main">{e(page.t['skip'])}</a>
{body}
</body>
</html>
"""
