# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-14 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner's standing answer for one-shot runs. |
| D2 | 2026-11-14 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist (Bandai/Toei), else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-11-14 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-14 | Abbreviations | engine work first (default), abbreviate | Engine work first (skill default; full names and terms). |
| D5 | 2026-11-14 | Graphics text left in Japanese | none (default), list | Translate all of it (titles, menus, banners, cards); leave the original Japanese logo only if it has no official English version. |
| D6 | 2026-11-14 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end. |
| D7 | 2026-11-14 | Existing saves / memory cards | use user's, none | None provided; build the debug tool as usual. |
| D8 | 2026-11-14 | Git identity | - | Already set by new-game.ps1; do not change it. |
| D9 | 2026-11-14 | Name for 帆船オルグ (worker call, pre-approved run) | Boat Org (fandom), Hansen Org (Hepburn), Sailing Ship Org (literal) | Sailing Ship Org: no official English name found; Org names are puns on the monster's motif, so the meaning beats a bare romanisation, and a fandom name is no source under D2. |
| D10 | 2026-11-14 | Skill process artifacts for phase 6 (worker call) | style reference + translator brief + batches.py, skip | Skipped: one 77-string batch done by the worker itself (Orca brief: no subagents). Create `docs/style-reference.md` (seed: glossary Tetomu rule) and `docs/translator-brief.md` before any later batch (phase 8 graphics text) goes to translator agents. |
| D11 | 2026-11-14 | Card table (Y_TITLE/21, CARDMS/0): growth and box budget never seen in game (worker call, pre-approved run) | keep it Japanese, translate with a guessed budget, hunt its screen further | Translate it (harmless if unused, right if some path shows it) with the guessed 232 px save-box budget; waived from the measured-budget and runtime-trace gates because no scene decodes it (docs/re/pac.md §Decode targets). lint names it as GUESSED on every run; revisit if a run ever decodes it. |
