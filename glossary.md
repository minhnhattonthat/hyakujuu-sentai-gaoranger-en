# Glossary - Hyakujuu Sentai GaoRanger (PS1)

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Kakeru-san). Name order: Western (given name first).
- Romanisation source: official English names (Bandai/Toei) where they exist, else an earlier fan patch, else Hepburn without macrons.
- Credits: English.
- Register / flavour: plain modern English, light Super Sentai flavour (show terms kept). No sound effects in the text.
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening.

## Style rules
- Punctuation map: 「」 -> "..." (ASCII quotes; the 「」 cells are 12 px Japanese glyphs), 『』 -> '...',
  ・・・ / … -> ..., ！！ -> !!, ！？ -> !?, 〜 -> ~. ♪ stays (font cell).
- Tetomu speaks every story, save, load and option line: warm, earnest; formal のです -> imperative/"you must",
  casual わ/ね/よ -> contractions, "okay?". The card table (CARDMS / Y_TITLE/21) is neutral system text, no quotes,
  except card-0446 (よむわ: Tetomu's voice, "I'll read...").
- Memory-card wording follows Sony's: "Memory Card", "remove or insert", "format", "overwrite".

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| テトム | Tetomu | | Gao shrine maiden; never named in the game text | Tetom |
| ガオレンジャー | GaoRanger(s) | | team: plural when addressed, singular as an adjective ("GaoRanger save file") | Gaorangers, Gaoranger |
| ガオのせんし | warriors of Gao | | | Gao soldiers |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| オルグ | Org(s) | | | Orug, Orgue |
| はんせんオルグ | Sailing Ship Org | | 帆船オルグ; no official English name found, so the literal meaning (D9) | Boat Org, Hansen Org |
| ブルドーザーオルグ | Bulldozer Org | | | |
| ハイネスデュークオルグ | Highness Duke Org | | | Highness Duke Ogre |
| じゃあくなおに | wicked ogres | | the Orgs (Ogre Tribe Org) | demons |
| ガオのせいれい | spirits of Gao | | the Power Animals | |
| オルグはんのう / はんのう | Org reading / reading | | Tetomu's sensor | reaction |
| メモリーカード | Memory Card | | | memory card |

## Decisions from earlier batches
- p6 review (codex, Important on card-0446): the reviewer flagged "I'll read..." as breaking the neutral card-table
  rule. Ruling: JP よむわ is Tetomu's voice, so the line keeps "I'll" and the style rule above names the exception.
- p6 (whole script, one batch, translated by the phase-6 worker): card choices keep the cursor cell `○` (12 px);
  the unselected side gets 3 ASCII spaces (4 px each) so "No"/"Yes" stay put when the cursor moves.
