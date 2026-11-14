# Hyakujuu Sentai GaoRanger (PS1) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md; `python tools/skill.py` prints it). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Setup once: `git config core.hooksPath tools/hooks`
- Build:    `python -X utf8 tools/build.py`  -> build/gaoranger_en.cue/.bin (checks the dump against `rom.sha1` first)
- Check:    `python -X utf8 tools/check.py`  (tests + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/gaoranger_en.cue --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 tools/debug/warp.py <scene>.. [--cue build/gaoranger_en.cue] [--state]` -> `work/qa/warp/<scene>/` (`--list`; `--all` regenerates every scene, exit 1 on a miss; scenes: `tools/debug/scenes.txt`; never ask the user to play to a scene)
- Text:     `tools/lint.py` (budgets), `tools/jpleft.py` (Japanese left), `build.py --marker | --qa ID=TEXT`; coverage: `warp.py .. --script tools/lua/textptr.lua --var HOLD=0` + `tools/textcov.py DIR`
- Release:  `python -X utf8 tools/release.py` (xdelta vs the .bin + verify; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original disc: `rom/Hyakujuu Sentai GaoRanger (Japan).cue/.bin` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Track 2 is CD audio.
- Emulator: this repo's own PCSX-Redux in `tools/pcsx/` (nightly 31258.20261113, via `fetch_emu.py pcsx`; gitignored). BIOS: `tools/bios/scph5500.bin` (`fetch_emu.py psx-bios`, picked up by emu.py). Disc tools: `tools/mkpsxiso/` (mkpsxiso/dumpsxiso v2.30, github.com/Lameguy64/mkpsxiso), `tools/armips/` (v0.11.0, github.com/Kingcom/armips). Savestates: `work/states/`.
- Text: `script/`. Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the agent types (translator, reviewer, visual-qa, playtester, graphics) shipped by the plugin as `translate-retro-game:<type>` (Claude Code), `.codex/agents/` (Codex) or `.opencode/agents/` (opencode), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Japanese game: confirm is circle (`--mash-key circle`). Real BIOS needed for scene work (OpenBIOS only for smoke).
- Recon setup in a fresh clone: dump the disc (docs/re/disc.md), then `python -X utf8 tools/unpack_all.py` -> `work/pac/`.
- `tbl/jp.tbl` is generated: edit the rows in `tools/make_tbl.py`, then run it. Glyphs are BE u16 (docs/re/text.md).
- Files are found by name through the EXE's file table (docs/re/disc.md, flow.md); prove a moved file loads before relying on it.
- Skill gotchas hit here: `docs/skill-gotchas.md`.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
