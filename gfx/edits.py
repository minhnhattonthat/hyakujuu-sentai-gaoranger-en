"""Graphics text edits: tools/gfx_edit.py applies them, build.py writes every copy (tools/gfx.py copies()).

EDITS = {sha1 prefix of the original TIM (work/gfx/sweep/index.tsv): (CLUT row for previews, [edit, ...])}
An edit is {"rect": (x, y, w, h), "text": "...", font/size/xscale/...} (gfx_edit.label) or {"rect": .., "clear": True}.
Rects are the Japanese label's ink box; label classes keep one font and size each (references/graphics.md).
"""

BIG = dict(font="anton", tracking=1)  # 24 px menu titles (orange gradient, dark outline)
PLATE = dict(font="sans-b")  # 16 px speaker name plates (Anton closed its counters at this size)
SMALL = dict(font="sans-b")  # red 16-19 px option values
TITLE = dict(font="sans-b", size=14)  # 19-20 px title wheel items (lime, white top, dark outline)
GLOW = [10, 6, 4, 3, 2, 2, 1, 1]  # game over logo: ramp index by distance from the letters (core = 15)
MENU20 = dict(font="anton", size=16, tracking=1)  # game-over choices (orange gradient, dark outline), caps
GAMEOVER_TOP = [  # rows 0-110: the same pixels in the action (TIM 7) and robo (TIM 96) game-over pages
    {"rect": (0, 0, 225, 64), "text": "GAME OVER", "font": "anton", "fill": 15, "glow": GLOW, "tracking": 2},
    {"rect": (225, 0, 31, 26), "clear": True},  # the separate long-vowel bar after バ
    # drips under バー (logo tails; the robo game over still showed them under OVER)
    {"rect": (162, 64, 94, 14), "clear": True},
    {"rect": (182, 80, 58, 11), "clear": True},
    {"rect": (182, 96, 60, 12), "clear": True},
    # the logo sprite also shows rows 64-69 of the left half, so the first choice keeps those rows empty
    {"rect": (0, 66, 127, 4), "clear": True},
    {"rect": (0, 70, 127, 16), "text": "KEEP FIGHTING", **MENU20},
    {"rect": (2, 90, 156, 20), "text": "GIVE UP", **MENU20},
]

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
    # TIM 7: A_*.PAC 16_3, action-stage game over + continue (two sets of choices: plain and on highlight bars)
    "15223a096500": (0, GAMEOVER_TOP + [
        {"rect": (137, 112, 96, 24), "text": "CONTINUE", **MENU20},  # をつづける (seen only as a texture so far)
        {"rect": (42, 161, 155, 14), "text": "PRESS START!!", "font": "sans-b", "ring": 0},
        {"rect": (0, 178, 127, 20), "text": "KEEP FIGHTING", **MENU20},
        {"rect": (2, 202, 156, 20), "text": "GIVE UP", **MENU20},
        {"rect": (1, 224, 96, 24), "text": "CONTINUE", **MENU20},
    ]),
    # TIM 96: BC_ST07 1_12_3, robo game over: rows 112+ hold other data, only the top part is the same as TIM 7
    "b5b4009e7a6c": (0, GAMEOVER_TOP),
    # TIM 159: O_TITLE 11, Y_TITLE 12_3: title wheel and its submenus. Some items are built from pieces drawn side
    # by side: オルゲット|ゆったり|ドッ+キリ + ファイト (first part right-aligned, ファイト left-aligned, so any pair
    # reads as one label), データ+の+ロ+ード (one composite). TEST USER (debug) and the frame parts stay.
    "9e381e7c8f83": (0, [
        {"rect": (10, 9, 155, 14), "text": "PRESS START!!", **TITLE, "ring": 0},
        {"rect": (8, 25, 80, 20), "text": "Orgette ", **TITLE, "align": "r"},  # ト ends at x 87, ド starts at 88
        {"rects": [(88, 25, 32, 20), (8, 81, 32, 20)], "text": "Thrill ", **TITLE, "align": "r"},  # ドッキリ
        {"rect": (12, 105, 96, 20), "text": "New Game", **TITLE},
        {"rects": [(111, 115, 56, 19), (136, 203, 26, 19), (162, 203, 13, 19), (200, 227, 34, 19)],
         "text": "Load Data", **TITLE},
        {"rect": (10, 129, 98, 20), "text": "Continue", **TITLE},
        {"rect": (11, 154, 74, 19), "text": "Sound", **TITLE},
        {"rect": (88, 154, 63, 19), "text": "Fight", **TITLE, "align": "l"},
        {"rect": (9, 178, 55, 19), "text": "Vibration", **TITLE, "xscale": 0.85},
        {"rect": (64, 178, 87, 19), "text": "Relaxed ", **TITLE, "align": "r"},
        {"rect": (8, 200, 127, 11), "text": "©2001 TV Asahi / Toei", "font": "sans-b", "ring": 0},
        {"rect": (11, 226, 81, 19), "text": "Easy", **TITLE},
        {"rect": (100, 226, 97, 20), "text": "Hard", **TITLE},
    ]),
}
