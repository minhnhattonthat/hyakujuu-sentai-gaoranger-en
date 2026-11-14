# Hyakujuu Sentai GaoRanger English translation

Unofficial English fan translation of **Hyakujuu Sentai GaoRanger** (PlayStation, Bandai / Natsume, 2001,
SLPS-03353): the source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
or memory card file helps most.

## Translation status

| Part | Status |
|---|---|
| Story briefings (Tetomu) | Translated |
| Save, load, option and Memory Card messages | Translated |
| Menus, title-screen wheel, speaker name plates, chapter banners, CHANCE!, GAME OVER, THE END | Translated (redrawn graphics) |
| FMV robot-name captions | Translated (re-encoded video frames) |
| Staff credits roll | Translated (rebuilt in English) |
| Title logo | Left in Japanese (no official English logo) |
| Brush hit effects (斬, 破, 滅...), FMV brush calligraphy | Kept as artwork |
| Spoken lines (FMVs, in-game voice clips) | English subtitles over the Japanese audio |
| Theme song | Japanese audio |

Known issues: some staff names in the credits are read from the kanji (no English credit found; `docs/polish.md`);
the action-stage game-over screen shares the robo one's redraw but was never reached in testing. See
[Issues](../../issues).

Tested in PCSX-Redux (SCPH-5500 BIOS). Start from a cold boot: savestates from the Japanese game keep its old text.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `gfx/` | Graphics-text edits (menus, plates, banners, credits). |
| `tools/` | Python build chain: extract, insert, graphics, FMV captions, lint, verify, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.codex/agents/`, `.opencode/agents/` | Subagent types (translator, reviewer, visual QA, playtester, graphics) for Codex and opencode; Claude Code gets them from the plugin. |

## Build your own patched disc

Needs Python 3.12+ and your own BIN/CUE dump of the Japanese disc.

```sh
git clone https://github.com/minhnhattonthat/hyakujuu-sentai-gaoranger-en
cd hyakujuu-sentai-gaoranger-en
# copy your dump to: rom/Hyakujuu Sentai GaoRanger (Japan).bin + .cue
#   (.bin: 183543024 bytes, SHA-1 20df603f974150fa3f9198d11b17f54afeeb4cd4;
#    .cue: SHA-1 58df6ad2db8fde7d32e6ccc6999616cabb92a8e8; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/build.py                          # -> build/gaoranger_en.cue/.bin
python -X utf8 tools/check.py                          # tests + text lint
```

The build also needs mkpsxiso 2.30 and armips 0.11.0 in `tools/` (see `AGENTS.md`).

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Bandai's and is included only so the
translation can be checked against it. Hyakujuu Sentai GaoRanger is (c) 2001 TV Asahi / Toei and (c) Bandai 2001;
this project is not affiliated with them. Do not share patched images.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
