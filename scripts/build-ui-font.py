#!/usr/bin/env python3
"""Draws the interface pieces and writes the fonts that place them.

Minecraft has no way to draw a box on the screen. What it does have is text, and a resource
pack can say what any character looks like - so a panel is a character whose picture happens to
be a rounded rectangle, and a layout is a line of text with characters that move the cursor
backwards. That is the whole trick behind every "custom UI" server, and everything below is
bookkeeping around those two facts.

Three things come out of here:

  * `assets/landmc/textures/font/ui/*.png` - one image per panel, drawn to the pixel.
  * `assets/landmc/font/ui.json` - which character shows which image, and where it sits.
  * `assets/landmc/font/space.json` - characters that only move the cursor, forwards or back.

The codepoints are in the private use area, which exists precisely so that nothing else claims
them. They are assigned in the order the panels are declared and written into a small manifest
the plugins read, so nobody has to type `\\uE001` into a config and hope.

Run after changing PANELS, then scripts/build-resourcepack.py to publish the result.
"""
import json
import pathlib
import struct
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACK = ROOT / "resourcepack" / "pack"
NAMESPACE = "landmc"

TEXTURES = PACK / "assets" / NAMESPACE / "textures" / "font" / "ui"
FONTS = PACK / "assets" / NAMESPACE / "font"
MANIFEST = ROOT / "resourcepack" / "ui-glyphs.json"

# Where the panels' codepoints start. U+E000 is the first private use character.
FIRST_CODEPOINT = 0xE000

# The offsets the space font provides, doubled each time. Any whole number of pixels is the sum
# of a few of these, which is why this handful covers every layout instead of one glyph per
# distance.
SPACE_STEPS = (1, 2, 4, 8, 16, 32, 64, 128, 256)

# Where the negative and positive space characters live, after the panels.
SPACE_BASE = 0xE900


def rounded_panel(width, height, radius, colour):
    """An RGBA bitmap of a rounded rectangle, as rows of (r, g, b, a) tuples.

    Corners are cut rather than smoothed. Minecraft draws a font at whatever scale the GUI is
    set to, and a half-transparent antialiased edge turns into a grey fringe at 3x - the pixel art
    the rest of the game is drawn in does not have one either.
    """
    red, green, blue, alpha = colour
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            if _outside_corner(x, y, width, height, radius):
                row.append((0, 0, 0, 0))
            else:
                row.append((red, green, blue, alpha))
        rows.append(row)
    return rows


def _outside_corner(x, y, width, height, radius):
    if radius <= 0:
        return False

    # The centre of the arc for whichever corner this pixel is nearest, or None when the pixel
    # is in the straight part of an edge and no corner applies.
    centre_x = None
    if x < radius:
        centre_x = radius - 0.5
    elif x >= width - radius:
        centre_x = width - radius - 0.5

    centre_y = None
    if y < radius:
        centre_y = radius - 0.5
    elif y >= height - radius:
        centre_y = height - radius - 0.5

    if centre_x is None or centre_y is None:
        return False

    dx = x - centre_x
    dy = y - centre_y
    return dx * dx + dy * dy > radius * radius


def write_png(path, rows):
    """Writes an RGBA PNG. No filtering, no interlacing - these are tiny flat images."""
    height = len(rows)
    width = len(rows[0])

    raw = bytearray()
    for row in rows:
        raw.append(0)  # filter type 0: none
        for pixel in row:
            raw.extend(pixel)

    def chunk(kind, payload):
        data = kind + payload
        return (struct.pack(">I", len(payload)) + data
                + struct.pack(">I", zlib.crc32(data) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


# name, width, height, corner radius, ascent, RGBA
#
# Sizes are game pixels at GUI scale 1, which is the unit the font system measures in.
#
# Ascent is how far above the text baseline the image starts, and it is the field that decides
# whether a panel sits behind its line or floats above it. A glyph is drawn from
# `baseline - ascent` downwards, so a background wants a small ascent - a few pixels above the
# letters - and gets its height from going down, over the rows that follow. Giving a tall panel
# a tall ascent is what puts a black slab above the board instead of behind it.
#
# The colour is the one the old server drew its menus on: black at about 40%, dark enough to
# read white text against any world behind it.
PANELS = [
    # One panel for the whole sidebar, drawn on the title and reaching down past the last line.
    # Simpler than a piece per row and impossible to misalign: there is only one of it.
    #
    # It has a second job besides looking like a panel, which is covering the box the client
    # draws behind a sidebar. That box is filled in code rather than taken from a texture, so
    # no image in a pack replaces it - but text is drawn after it, and a panel is text. Hence
    # the width, which is the widest line the board has plus a margin either side, and hence
    # the colour, which is not black: the box underneath is, and black over black only gets
    # darker. A panel with some light in it is the only thing that lifts the result off that
    # floor.
    # Translucent again: with the client's own box discarded by the core shader there is
    # nothing black underneath to fight, so this sits on the world the way it looks like it
    # should. If the shader ever stops applying, this goes back up - see the note in gui.vsh.
    ("sidebar", 132, 108, 6, 12, (0, 0, 0, 120)),
    ("bar", 220, 30, 6, 22, (0, 0, 0, 106)),
]


def main():
    glyphs = {}
    providers = []

    # Cleared rather than written over. A panel dropped from the list leaves its image behind
    # otherwise, and a pack that ships glyphs no font refers to is a pack nobody can reason
    # about from its contents.
    if TEXTURES.is_dir():
        for stale in TEXTURES.glob("*.png"):
            stale.unlink()

    for index, (name, width, height, radius, ascent, colour) in enumerate(PANELS):
        codepoint = FIRST_CODEPOINT + index
        write_png(TEXTURES / f"{name}.png", rounded_panel(width, height, radius, colour))

        providers.append({
            "type": "bitmap",
            "file": f"{NAMESPACE}:font/ui/{name}.png",
            "height": height,
            "ascent": ascent,
            "chars": [chr(codepoint)],
        })
        glyphs[name] = {
            "char": chr(codepoint),
            "codepoint": f"U+{codepoint:04X}",
            "width": width,
            "height": height,
            "ascent": ascent,
        }

    FONTS.mkdir(parents=True, exist_ok=True)
    (FONTS / "ui.json").write_text(
        json.dumps({"providers": providers}, indent=2) + "\n", encoding="utf-8")

    advances = {}
    spaces = {}
    for step_index, step in enumerate(SPACE_STEPS):
        forward = SPACE_BASE + step_index
        backward = SPACE_BASE + 0x80 + step_index
        advances[chr(forward)] = step
        advances[chr(backward)] = -step
        spaces[f"+{step}"] = {"char": chr(forward), "codepoint": f"U+{forward:04X}"}
        spaces[f"-{step}"] = {"char": chr(backward), "codepoint": f"U+{backward:04X}"}

    (FONTS / "space.json").write_text(
        json.dumps({"providers": [{"type": "space", "advances": advances}]}, indent=2) + "\n",
        encoding="utf-8")

    MANIFEST.write_text(
        json.dumps({"font": f"{NAMESPACE}:ui", "spaceFont": f"{NAMESPACE}:space",
                    "panels": glyphs, "spaces": spaces}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    print(f"Wrote {len(PANELS)} panel(s) to {TEXTURES.relative_to(ROOT)}")
    print(f"Wrote {(FONTS / 'ui.json').relative_to(ROOT)} and {(FONTS / 'space.json').relative_to(ROOT)}")
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
