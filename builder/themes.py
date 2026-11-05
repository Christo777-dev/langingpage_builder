"""Design tokens for the four landing page themes.

A theme is a token set (palette, type, default button shape) plus a default
layout. Layouts only read CSS custom properties, so any layout can be paired
with any theme's tokens ("layout override").
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    key: str
    name: str
    blurb: str
    layout: str
    # Palette: page ground, tinted surface, text, action colour, text on action.
    bg: str
    soft: str
    ink: str
    accent: str
    accent_ink: str
    display_font: str
    body_font: str
    fonts_url: str
    button_shape: str
    # Extra per-theme CSS custom properties (type tuning).
    extra: str = ""


THEMES: dict[str, Theme] = {
    "organic": Theme(
        key="organic",
        name="Organisch",
        blurb="Weiche, atmende Formen, eine runde Serifenschrift, Salbei und Heidekraut.",
        layout="flow",
        bg="#EEF1E8",  # lichen mist
        soft="#D3DEC6",  # sage
        ink="#263328",  # forest floor
        accent="#6B4A6E",  # heather
        accent_ink="#FFFFFF",
        display_font="'Young Serif', 'Iowan Old Style', Georgia, serif",
        body_font="'Mulish', 'Segoe UI', system-ui, sans-serif",
        fonts_url=(
            "https://fonts.googleapis.com/css2?family=Young+Serif"
            "&family=Mulish:ital,wght@0,400..700;1,400&display=swap"
        ),
        button_shape="leaf",
        extra="--display-weight:400;--display-track:-0.01em;",
    ),
    "clinical": Theme(
        key="clinical",
        name="Klinisch",
        blurb="Sichtbares Raster, reines Schwarz-Weiß, ein Steckbrief wie auf einem Aufnahmebogen.",
        layout="grid",
        bg="#FFFFFF",
        soft="#F0F0F0",
        ink="#000000",
        accent="#000000",
        accent_ink="#FFFFFF",
        display_font="'Hanken Grotesk', 'Helvetica Neue', Arial, sans-serif",
        body_font="'Hanken Grotesk', 'Helvetica Neue', Arial, sans-serif",
        fonts_url=(
            "https://fonts.googleapis.com/css2?family=Hanken+Grotesk:"
            "ital,wght@0,400..700;1,400&display=swap"
        ),
        button_shape="square",
        extra="--display-weight:600;--display-track:-0.035em;",
    ),
    "luxury": Theme(
        key="luxury",
        name="Luxus",
        blurb="Vorspann wie im Kino, tiefes Nachtblau, gedämpftes Gold, eine elegante Serifenschrift.",
        layout="cinema",
        bg="#0F1B30",  # midnight navy
        soft="#18274A",
        ink="#EAE3D2",  # ivory
        accent="#C6A15B",  # muted gold
        accent_ink="#0F1B30",
        display_font="'Bodoni Moda', 'Didot', 'Bodoni 72', serif",
        body_font="'Jost', 'Futura', 'Century Gothic', sans-serif",
        fonts_url=(
            "https://fonts.googleapis.com/css2?family=Bodoni+Moda:"
            "ital,opsz,wght@0,6..96,400..700;1,6..96,400..700"
            "&family=Jost:wght@300..500&display=swap"
        ),
        button_shape="square",
        extra="--display-weight:400;--display-track:-0.01em;",
    ),
    "bold": Theme(
        key="bold",
        name="Kraftvoll",
        blurb="Diagonal geteilter Einstieg, breite fette Schrift, Indigo gegen Safrangelb.",
        layout="diagonal",
        bg="#FFFFFF",
        soft="#E6E1FA",  # lavender
        ink="#1F1846",  # indigo
        accent="#F4AE1A",  # saffron
        accent_ink="#1F1846",
        display_font="'Archivo', 'Arial Black', sans-serif",
        body_font="'Archivo', 'Helvetica Neue', Arial, sans-serif",
        fonts_url=(
            "https://fonts.googleapis.com/css2?family=Archivo:"
            "wdth,wght@62..125,300..900&display=swap"
        ),
        button_shape="slanted",
        extra="--display-weight:850;--display-track:-0.02em;--display-stretch:125%;",
    ),
}

LAYOUTS = {
    "flow": "Organisch fließend",
    "grid": "Klinisches Raster",
    "cinema": "Luxus-Kino",
    "diagonal": "Kraftvolle Diagonale",
}

BUTTON_SHAPES = {
    "pill": "Pille",
    "rounded": "Abgerundet",
    "square": "Eckig",
    "leaf": "Blatt",
    "slanted": "Schräg",
}


def readable_on(hex_color: str) -> str:
    """Return black or white, whichever reads better on the given colour."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    lum = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
    return "#000000" if lum > 0.179 else "#FFFFFF"
