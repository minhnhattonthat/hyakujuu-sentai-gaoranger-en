# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/vwf.txt | drawn for the Dual Orb translation by the same owner (MIT), copied 2026-11-14 | MIT, same as repo | yes | all game text (VWF, 12x16 font cells, tools/font.py) | `[ ] # * < > @ _` added; shadow added by font.py |
| fonts/LiberationSans-Bold.ttf, LiberationSans-Regular.ttf | github.com/liberationfonts/liberation-fonts release 2.1.5 | SIL OFL 1.1 (fonts/LICENSE-Liberation.txt) | yes | graphics text: name plates, small option values (tools/gfx_edit.py) | none (rendered without antialiasing) |
| fonts/Anton-Regular.ttf | github.com/google/fonts ofl/anton (2020) | SIL OFL 1.1 (fonts/OFL-Anton.txt) | yes | graphics text: 24 px menu titles, banners | none |
