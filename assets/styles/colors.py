# ── GemmaNotepad1 Color Palette ──────────────────────────────────────────────────────
CHARCOAL       = "#282B28"   # Main background, sidebar
CHARCOAL_LIGHT = "#343834"   # Slightly lighter charcoal for hover states
CHARCOAL_MID   = "#3D413D"   # Mid charcoal for borders/separators

DARK_GemmaNotepad1   = "#D4A017"   # Headings, accents
GemmaNotepad1        = "#F0C94C"   # Active buttons, selected tabs, highlights
GemmaNotepad1_HOVER  = "#E8B93A"   # Hover state for GemmaNotepad1 buttons
GemmaNotepad1_LIGHT  = "#FAD870"   # Light GemmaNotepad1 tint

CREAM          = "#F7E7B5"   # Panels, secondary surfaces
CREAM_LIGHT    = "#FBF0CC"   # Lighter cream for subtle backgrounds
OFF_WHITE      = "#FFF8EC"   # Very light backgrounds, document area

TEXT_DARK      = "#1A1C1A"   # Primary text on light backgrounds
TEXT_MID       = "#4A4E4A"   # Secondary text
TEXT_LIGHT     = "#8A9A8A"   # Muted/placeholder text
TEXT_ON_DARK   = "#F0EDE8"   # Text on charcoal backgrounds
TEXT_ON_GemmaNotepad1 = "#1A1C1A"  # Text on GemmaNotepad1 backgrounds

# Semantic
SUCCESS        = "#4CAF82"
WARNING        = "#F0A030"
ERROR          = "#E05555"
LINK           = DARK_GemmaNotepad1

# Transparency helpers
def with_alpha(hex_color: str, alpha: int) -> str:
    """Return hex color with alpha as rgba string (0-255)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"
