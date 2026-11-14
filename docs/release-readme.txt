Hyakujuu Sentai GaoRanger (PlayStation) - English translation patch v{version}
================================================================================

Unofficial English fan translation of Hyakujuu Sentai GaoRanger (PlayStation, Bandai / Natsume, 2001, SLPS-03353).
Not affiliated with Bandai, Natsume, Toei or TV Asahi. No game data is included: you need your own dump of the
Japanese disc. Please don't share patched images.

What you need
-------------
The Japanese disc as a BIN/CUE dump (Redump layout: one .bin with the data track and the CD-audio track):

  Hyakujuu Sentai GaoRanger (Japan).bin
    size   {base_size} bytes
    CRC32  {base_crc32}
    MD5    {base_md5}
    SHA-1  {base_sha1}
  Hyakujuu Sentai GaoRanger (Japan).cue
    SHA-1  {cue_sha1}

Any other dump (a different revision, an .iso with no audio track, an already patched copy) will not work.

How to patch
------------
1. Apply {patch} to the .bin with an xdelta3 patcher (Delta Patcher, xdelta UI, or the command line:
     xdelta3 -d -s "Hyakujuu Sentai GaoRanger (Japan).bin" {patch} "Hyakujuu Sentai GaoRanger (English).bin"
   ). The patched .bin is the same size as the original:
     CRC32  {built_crc32}
     SHA-1  {built_sha1}
2. Copy the original .cue next to it as "Hyakujuu Sentai GaoRanger (English).cue" and change its first line to
     FILE "Hyakujuu Sentai GaoRanger (English).bin" BINARY
   Nothing else in the .cue changes.
3. Load the .cue in your emulator. Start from a cold boot (power on), not from a savestate made on the Japanese
   game: savestates keep the old text and graphics. Memory Card saves carry over fine.

Tested in PCSX-Redux with the SCPH-5500 BIOS: every story chapter, all robo battles, the endings and credits,
the save, load and option screens, the Memory Card error messages and the Orgette Fight minigame.

Translation status
------------------
  Story briefings (Tetomu)                         English
  Save / load / option / Memory Card messages      English
  Menus, title screen wheel, speaker name plates   English (redrawn graphics)
  Chapter banners, CHANCE!, GAME OVER, THE END     English (redrawn graphics)
  FMV robot-name captions                          English (re-encoded video frames)
  Staff credits                                    English (rebuilt roll)
  Title logo                                       Japanese (no official English logo)
  Brush hit effects (斬, 破, 滅...) and FMV brush calligraphy   kept as artwork
  Voices, theme song                               Japanese audio

Known issues
------------
- Some staff names in the credits are read from the kanji (no English credit was found for them); corrections welcome.
- The action-stage game-over screen uses the same redraw as the robo one, but it was never reached in testing.
Report bugs at https://github.com/minhnhattonthat/hyakujuu-sentai-gaoranger-en/issues (a savestate or memory card
file helps most).

Credits
-------
Translation, hacking and tools: minhnhattonthat, with extensive AI assistance (Claude by Anthropic).
Text font: drawn for the same owner's Dual Orb translation (MIT licence); graphics fonts Anton and Liberation Sans (SIL Open Font Licence).
Hyakujuu Sentai GaoRanger (c) 2001 TV Asahi / Toei, (c) Bandai 2001.

Patch file SHA-1: {patch_sha1}
