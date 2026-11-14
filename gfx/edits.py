"""Graphics text edits: tools/gfx_edit.py applies them, build.py writes every copy (tools/gfx.py copies()).

EDITS = {sha1 prefix of the original TIM (work/gfx/sweep/index.tsv): (CLUT row for previews, [edit, ...])}
An edit is {"rect": (x, y, w, h), "text": "...", font/size/xscale/...} (gfx_edit.label) or {"rect": .., "clear": True}.
Rects are the Japanese label's ink box; label classes keep one font and size each (references/graphics.md).
"""

BIG = dict(font="anton", tracking=1)  # 24 px menu titles (orange gradient, dark outline)
# 16 px speaker name plates: one size for all, the largest at which SAILING SHIP ORG fits the 96 px sprite unsqueezed
# (squeezed Liberation Sans and Anton both close their D/O/A/R counters at this height)
PLATE = dict(font="sans-b", size=10)
SMALL = dict(font="sans-b")  # red 16-19 px option values
TITLE = dict(font="sans-b", size=14)  # 19-20 px title wheel items (lime, white top, dark outline)
GLOW = [10, 6, 4, 3, 2, 2, 1, 1]  # game over logo: ramp index by distance from the letters (core = 15)
MENU20 = dict(font="anton", size=16, tracking=1)  # game-over choices (orange gradient, dark outline), caps
BANNER = dict(font="anton", fill=15, glow=[13, 9, 6, 3, 2, 1, 1], tracking=1)  # story banners (white, ramp glow)
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
    # TIM 131: DE_ST*/DS_ST* 9_4, Y_* menus: menu titles, option values, story-box speaker plates.
    # Titles, plates and START LOADING use the sprite's u/v/w/h (13_17 groups, e.g. DS_ST01/Y_LOAD 13_17 @0d1e-0d72:
    # tools/sprgroups.py ... --tpage-x 6), not the JP ink box: ink outside the sprite is never shown, and a label
    # centred on the ink box sits off centre or loses its last letter.
    "f7a61f4b4498": (0, [
        # sprite u 24-135, but the panel behind it ends near u 130: keep the JP ink's width and centre (u 25-128)
        {"rect": (25, 48, 104, 24), "text": "LOAD DATA", **BIG},
        {"rect": (24, 48, 1, 24), "clear": True},  # the sprite's side strips (after: label() samples its rect)
        {"rect": (129, 48, 7, 24), "clear": True},
        {"rect": (16, 75, 40, 19), "text": "Yes", **SMALL},
        {"rect": (58, 75, 60, 19), "text": "No", **SMALL},
        {"rect": (25, 96, 104, 24), "text": "SAVE DATA", **BIG},
        {"rect": (24, 96, 1, 24), "clear": True},
        {"rect": (129, 96, 7, 24), "clear": True},
        {"rect": (24, 120, 88, 24), "text": "VIBRATION", **BIG, "xscale": 0.85},
        {"rect": (24, 144, 88, 24), "text": "SOUND", **BIG},
        {"rect": (15, 172, 65, 17), "text": "Stereo", **SMALL},
        {"rect": (90, 172, 67, 17), "text": "Mono", **SMALL},
        {"rect": (17, 195, 37, 20), "text": "On", **SMALL},
        {"rect": (56, 195, 40, 20), "text": "Off", **SMALL},
        {"rect": (144, 0, 96, 16), "text": "KING ORG", **PLATE},
        {"rect": (144, 16, 96, 16), "text": "RASETSU", **PLATE},
        {"rect": (144, 32, 96, 16), "text": "SHUTEN", **PLATE},
        {"rect": (144, 48, 96, 16), "text": "ROUKI", **PLATE},
        {"rect": (144, 64, 96, 16), "text": "BULLDOZER ORG", **PLATE},
        {"rect": (144, 80, 96, 16), "text": "SAILING SHIP ORG", **PLATE},
        {"rect": (136, 96, 112, 24), "text": "START LOADING", **BIG},
    ]),
    # TIM 7: A_*.PAC 16_3, action-stage game over + continue (two sets of choices: plain and on highlight bars)
    "15223a096500": (0, GAMEOVER_TOP + [
        # をつづける: the pause menu's sprite shows u 152-239 only (つづける, after たたかい: SPRITE_FIXES)
        {"rect": (137, 112, 15, 24), "clear": True},
        {"rect": (152, 112, 88, 24), "text": "CONTINUE", **MENU20},
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
        # しんどう's sprite is u 8-79 (Y_TITLE 13 @0x7f4), ゆったり's u 80-151 (@0x900)
        {"rect": (8, 178, 72, 19), "text": "Vibration", **TITLE},
        {"rect": (80, 178, 71, 19), "text": "Relaxed ", **TITLE, "align": "r"},
        {"rect": (8, 200, 127, 11), "text": "©2001 TV Asahi / Toei", "font": "sans-b", "ring": 0},
        {"rect": (11, 226, 81, 19), "text": "Easy", **TITLE},
        {"rect": (100, 226, 97, 20), "text": "Hard", **TITLE},
    ]),
    # TIM 136: DS_ST01/04, DE_ST03-05 4: story banners, one 48 px line of two pieces each (name + 誕生/覚醒; sprite
    # groups in the PAC's 12_17 leaf, tools/sprgroups.py), CLUT rows 0-5 = orange/green/purple variants
    "cb0cf6ab0650": (0, [
        {"rects": [(0, 0, 248, 48), (192, 48, 56, 48)], "text": "GAOMUSCLE STRIKER IS BORN!", **BANNER},
        {"rects": [(0, 96, 224, 48), (168, 144, 72, 48)], "text": "GAOICARUS IS BORN!", **BANNER},
        {"rects": [(0, 192, 216, 48), (0, 144, 88, 48)], "text": "GAOSILVER AWAKENS!", **BANNER},
    ]),
    # TIM 154: DE_ST07E 9_3, おわり after the credits (red, white rim, grey glow)
    "69ccdfb64f5e": (0, [
        {"rect": (0, 0, 80, 32), "text": "THE END", "font": "anton", "fill": 8, "glow": [15, 12, 7, 3, 1],
         "tracking": 1},
    ]),
    # TIM 77: robo battles 1_14_5, 好機 (chance to strike) prompt: white letters, purple glow; the rest are effects
    "8fb456fd1084": (0, [
        {"rect": (60, 99, 90, 46), "text": "CHANCE!", "font": "anton", "fill": 15, "glow": [10, 7, 5, 3, 2, 1],
         "tracking": 1},
    ]),
    # TIM 5: A_*.PAC 15_4, action-stage HUD: オルゲット label beside the counter digits
    "d352ef235210": (0, [
        {"rect": (105, 65, 108, 39), "text": "ORGETTE", "font": "sans-b"},
    ]),
}

# Sprite groups rewritten in place (gfx_edit.sprite_fix): (old sprites, new sprites) as (x, y, u, v, w, h, tpage),
# clut kept; a zeroed sprite draws nothing (as in the credits).
# Pause menu "continue" = たたかい (u 0-95 of the GIVE UP row, TIM 7) + つづける (u 152-239): no English word pair
# shares a first half, so the first piece goes and CONTINUE is centred on its own.
SPRITE_FIXES = [
    ([(-92, -12, 0, 88, 96, 24, 0x200f), (4, -12, 152, 112, 88, 24, 0x200f)],
     [(0, 0, 0, 0, 0, 0, 0x200f), (-44, -12, 152, 112, 88, 24, 0x200f)]),
]
_A = "DEMO EX01 EX02 EX03 EX04 EX05 EX06 EX07 EX08 EX09 EX10 ST010 ST11 ST12 ST21 ST22 ST31 ST32 ST41 ST42 ST51 ST52 ST53"
_B = "BB_ST00B BB_ST00C BB_ST01B BB_ST02B BC_ST07 B_ST00 B_ST01 B_ST02 B_ST03 B_ST04 B_ST05 B_ST06 B_ST07"
SPRITE_LEAVES = ([f"A_{p}.PAC/16_1" for p in _A.split()] + [f"{p}.PAC/1_12_1" for p in _B.split()]
                 + ["Y_IVENT.PAC/0_13"])  # every leaf holding the group (two copies each: plain + highlight clut)
