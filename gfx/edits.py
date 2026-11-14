"""Graphics text edits: tools/gfx_edit.py applies them, build.py writes every copy (tools/gfx.py copies()).

EDITS = {sha1 prefix of the original TIM (work/gfx/sweep/index.tsv): (CLUT row for previews, [edit, ...])}
An edit is {"rect": (x, y, w, h), "text": "...", font/size/xscale/...} (gfx_edit.label) or {"rect": .., "clear": True}.
Rects are the Japanese label's ink box; label classes keep one font and size each (references/graphics.md).
"""

BIG = dict(font="anton", tracking=1)  # 24 px menu titles (orange gradient, dark outline)
PLATE = dict(font="sans-b")  # 16 px speaker name plates (Anton closed its counters at this size)
SMALL = dict(font="sans-b")  # red 16-19 px option values

EDITS = {
    # TIM 131: DE_ST*/DS_ST* 9_4, Y_* menus: menu titles, option values, story-box speaker plates
    "f7a61f4b4498": (0, [
        {"rect": (20, 48, 110, 24), "text": "LOAD DATA", **BIG},
        {"rect": (16, 75, 40, 19), "text": "Yes", **SMALL},
        {"rect": (58, 75, 60, 19), "text": "No", **SMALL},
        {"rect": (20, 96, 110, 24), "text": "SAVE DATA", **BIG},
        {"rect": (20, 120, 110, 24), "text": "VIBRATION", **BIG},
        {"rect": (20, 144, 110, 24), "text": "SOUND", **BIG},
        {"rect": (15, 172, 65, 17), "text": "Stereo", **SMALL},
        {"rect": (90, 172, 67, 17), "text": "Mono", **SMALL},
        {"rect": (17, 195, 37, 20), "text": "On", **SMALL},
        {"rect": (56, 195, 40, 20), "text": "Off", **SMALL},
        {"rect": (143, 0, 106, 16), "text": "KING ORG", **PLATE},
        {"rect": (143, 16, 106, 16), "text": "RASETSU", **PLATE},
        {"rect": (143, 32, 106, 16), "text": "SHUTEN", **PLATE},
        {"rect": (143, 48, 106, 16), "text": "ROUKI", **PLATE},
        {"rect": (143, 64, 106, 16), "text": "BULLDOZER ORG", **PLATE},
        {"rect": (143, 80, 106, 16), "text": "SAILING SHIP ORG", **PLATE},
        {"rect": (142, 96, 107, 24), "text": "START LOADING", **BIG},
    ]),
}
