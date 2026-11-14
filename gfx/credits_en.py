"""English staff roll: tools/credits.py packs these lines into the DE_ST07 atlases and rewrites the 12_17 groups.

GROUPS = {group: [(x, y, text, style, align), ...]}: screen offsets from the centre (320x240 view), y = the line's
top (16 px strips), align l/c/r = x is the left edge / centre / right edge. style NAME = white, ROLE = orange (the
game's CLUT rows). Positions follow the Japanese layout (docs/re/graphics.md §Credits layout). Names: Western order
(D1), official spellings where known (D2); readings guessed from kanji are listed in docs/polish.md.
"""

NAME, ROLE = "name", "role"
TOEI = "(Toei Company, Ltd.)"


def pair(y, left, right, style=NAME):
    """Cast-style row: role right-aligned before the centre, name left-aligned after it."""
    return [(-8, y, left, style, "r"), (8, y, right, NAME, "l")]


def c(y, text, style=NAME):
    return [(0, y, text, style, "c")]


def l(x, y, text, style=NAME):
    return [(x, y, text, style, "l")]


BIG = {"text": "STAFF", "font": "anton", "tracking": 1}  # g20: 96x24 title (TIM 148 0,0), relabelled in place

GROUPS = {
    11: c(-104, "Voice Cast", ROLE),
    21: pair(-72, "Gao Red", "Noboru Kaneko"),
    22: pair(-48, "Gao Yellow", "Kei Horie"),
    23: pair(-24, "Gao Blue", "Takeru Shibaki"),
    24: pair(0, "Gao Black", "Kazuyoshi Sakai"),
    25: pair(24, "Gao White", "Mio Takeuchi"),
    26: pair(56, "Tetomu", "Takemi"),
    27: pair(80, "Gao Madillo", "Chiaki Maeda"),
    28: pair(-64, "Yabaiba", "Koichi Sakaguchi"),
    29: pair(-32, "TsueTsue", "Rei Saito"),
    30: pair(8, "Sailing Ship Org", "Hidenari Ugaki"),
    31: pair(40, "Bulldozer Org", "Dai Matsumoto"),
    32: pair(-72, "Shuten", "Tetsu Inada"),
    33: pair(-40, "Rouki", "Eiji Takemoto"),
    34: pair(-8, "Rasetsu (male)", "Hidekatsu Shibata") + pair(16, "Rasetsu (female)", "Hiromi Nishikawa"),
    35: pair(48, "King Org", "Hisanori Koyatsu"),
    36: pair(-8, "Narrator", "Hiroshi Masuoka"),
    37: l(-112, -56, "Director", ROLE),
    38: l(8, -56, "Mitsuo Matsumoto"),
    39: l(-112, -8, "Programmers", ROLE),
    40: l(8, -8, "Hirohisa Ota"),
    41: l(8, 16, "Seiji Noda"),
    42: l(8, 40, "Kazuto Yamada"),
    43: l(-88, -40, "Sound", ROLE) + l(24, -40, "Hiroyuki Iwatsuki"),
    44: l(-88, 24, "Support", ROLE) + l(24, 24, "Toshiyasu Miyabe"),
    45: l(-136, -56, "General Supervisor", ROLE) + l(0, -56, "Jun Hikasa") + l(0, -32, TOEI),
    46: l(-136, 16, "Supervisor", ROLE) + l(0, 16, "Takaaki Utsunomiya") + l(0, 40, TOEI),
    47: c(-88, "In Cooperation With", ROLE),
    48: c(-40, "Toei Company, Ltd."),
    49: c(-8, "Nippon Columbia Co., Ltd."),
    50: c(24, "TV Asahi Music Co., Ltd."),
    51: c(56, "Showa Note Co., Ltd."),
    52: c(-56, "Seika Co., Ltd."),
    53: c(-24, "Plex Co., Ltd."),
    54: c(8, "Kodansha Ltd."),
    55: c(40, "Shogakukan Inc."),
    56: c(-64, "Developed by", ROLE) + c(-40, "Natsume Co., Ltd. Nagoya Office"),
    57: c(8, "Produced by", ROLE) + c(32, "Bandai Co., Ltd."),
    58: c(-24, "© 2001 TV Asahi / Toei"),
    59: c(8, "© BANDAI 2001"),
    60: c(-88, "Theme Song", ROLE),
    61: c(-48, "“GaoRanger Hoero!!”"),
    62: pair(-16, "Lyrics", "Nagae Kuwabara"),
    63: pair(8, "Composed & Arranged", "Kotaro Nakagawa"),
    64: pair(32, "Vocals", "Yukio Yamagata"),
    65: c(-24, "Executive Producer", ROLE),
    66: c(8, "Shin Unozawa"),
    67: l(-136, 32, "Producers", ROLE),
    68: l(16, 32, "Masazumi Kato"),
    69: l(16, 56, "Kimihiko Igaya"),
    70: c(-64, "Special Thanks", ROLE),
    71: c(-32, "Junki Takegami"),
    72: pair(4, "Satoshi Shinohara", TOEI),
    73: pair(32, "Naomi Matsuyama", TOEI),
    74: pair(60, "Yuichi Kushima", TOEI),
    75: c(-88, "Kenji Taniyama"),
    76: c(-64, "Tadashi Yamazaki"),
    77: c(-40, "Takeshi Inoue"),
    78: c(-16, "Kenji Hatakeyama"),
    79: c(8, "Hideyuki Oi"),
    80: c(48, "Fuyuki Nishizawa"),
    81: c(72, "Rio Nakata"),
    82: c(-56, "Orgettes"),
    83: l(-112, -24, "Toru Omura") + l(24, -24, "Katsumi Shiono"),
    84: l(-112, 0, "Minoru Yokosuka") + l(24, 0, "Ryohei Haya"),
    85: l(-112, 24, "Daisaku Arima") + l(24, 24, "Hidenori Nakayama"),
    86: l(-136, -88, "Chief Producers", ROLE),
    87: l(16, -64, "Takashi Aoyama"),
    88: l(16, -40, "Seiko Fujisawa"),
    89: l(16, -16, "Tomoaki Imanishi"),
    90: l(-112, -56, "Designers", ROLE),
    91: l(8, -56, "Shunichi Taniguchi"),
    92: l(8, -32, "Kunio Suzuki"),
    93: l(8, -8, "Takashi Shinbo"),
    94: l(8, 16, "Yutaka Inagaki"),
    95: l(8, 40, "Aya Kamimura"),
}
