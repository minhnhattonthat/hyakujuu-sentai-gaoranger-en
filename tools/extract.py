"""extract.py: dump every string table (docs/re/text.md) from the ORIGINAL disc tree to script/<name>.json.

One JSON per unique table; identical tables in several files (the save table is in 7 PACs) share one JSON whose
"files" lists them all, so insertion writes the same table to each. Never overwrites an existing JSON
(`--force` rewrites the jp fields only, keeping en/notes by id).

Table layout: u16 a, u16 count, count x u16 offsets (an offset = table size is an empty end slot), then strings:
glyphs + control codes (tbl/jp.tbl) ending in FF, each followed by zero padding; every string starts 2-aligned.
JSON per string: id (<name>-<orig offset>), slots (entry indexes that point at it; [] = unreferenced, kept),
jp, en, pad (zero bytes after FF), notes.

    python -X utf8 tools/extract.py [--force]      # writes script/*.json
    python -X utf8 tools/extract.py --check        # rebuild every table from its jp fields == original bytes
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pac  # noqa: E402
from tbl import Table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "work" / "disc" / "tree" / "DATA"
SCRIPT = ROOT / "script"
TBL = Table.load(ROOT / "tbl" / "jp.tbl")

# name -> files holding that exact table (found by textscan.py over every leaf; test_extract checks none is missed)
TABLES = {
    **{f"ds0{i}": [f"DS_ST0{i}.PAC/13_12"] for i in range(1, 8)},  # story intermission dialogue
    "save": [f"DE_ST0{i}.PAC/14_13_1" for i in range(1, 6)] + ["Y_EDSAVE.PAC/14_13_1", "Y_SAVE.PAC/14_13_1"],
    "load": ["Y_LOAD.PAC/13_13_1"],
    "card": ["CARDMS.PAC/0", "Y_TITLE.PAC/21"],  # memory-card messages
    "option": ["Y_OPTION.PAC/13_12"],
    "title": ["Y_TITLE.PAC/20"],  # title/option labels + debug user names
    "title_debug": ["Y_TITLE.PAC/22"],  # debug user / save labels, 21-glyph ruler
    "debug": ["O_TITLE.PAC/1"],  # leftover debug menu
    "system": ["O_TITLE.PAC/2"],  # system messages (memory card, high score)
}


def leaf(name):
    """Bytes of leaf 'PAC/path' (path as unpack_all.py names it: slot numbers, 'z' = into an lzs payload)."""
    f, path = name.split("/")
    d = (DATA / f).read_bytes()
    for part in path.split("_"):
        if part == "z":
            continue  # the lzs node before it was already decoded
        entries = {i: (o, s) for i, o, s in pac.add_entries(d, 0)}
        o, s = entries[int(part)]
        d = pac.lzs_decode(d, o)[0] if pac.kind(d, o) == "lzs" else d[o:o + s]
    return d


def parse(d):
    """Table bytes -> dict (see module doc). Raises if any byte isn't header, string or zero padding."""
    a, n = struct.unpack_from("<HH", d, 0)
    offs = struct.unpack_from(f"<{n}H", d, 4)
    refs = sorted(set(offs) - {len(d)})

    def next_start(p):
        """Next string start at or after p: a referenced offset, or (unreferenced string in a non-zero gap)
        the even position at/just before the first non-zero byte. A glyph's high byte can be 00, so zeros
        alone don't end padding."""
        nxt = min([o for o in refs if o >= p], default=len(d))
        q = p
        while q < nxt and d[q] == 0:
            q += 1
        return nxt if q == nxt else q & ~1

    pos = next_start(4 + 2 * n)
    lead = pos - (4 + 2 * n)
    strings = []
    while pos < len(d):
        text, used = TBL.decode(d, pos)
        end = pos + used
        p = next_start(end)
        if p < end or (p > end and set(d[end:p]) != {0}):
            raise ValueError(f"string at {pos:#x} runs into the next at {p:#x}")
        strings.append({"id": None, "off": pos, "slots": [i for i, o in enumerate(offs) if o == pos],
                        "jp": text[:-len("{end}")], "en": "", "pad": p - end, "notes": ""})
        pos = p
    missed = set(refs) - {s["off"] for s in strings}
    if missed:
        raise ValueError(f"offsets not at a string start: {sorted(missed)}")
    return {"a": a, "count": n, "lead": lead, "end_slots": [i for i, o in enumerate(offs) if o == len(d)],
            "strings": strings}


def build(t, field="jp"):
    """Table dict -> bytes, from each string's `field` (falls back to jp when empty). Keeps every string 2-aligned."""
    body = bytearray(bytes(4 + 2 * t["count"] + t["lead"]))
    offs = [0] * t["count"]
    for s in t["strings"]:
        for i in s["slots"]:
            offs[i] = len(body)
        body += TBL.encode((s.get(field) or s["jp"]) + "{end}")
        body += bytes(s["pad"] + (len(body) + s["pad"]) % 2)
    for i in t["end_slots"]:
        offs[i] = len(body)
    struct.pack_into(f"<HH{t['count']}H", body, 0, t["a"], t["count"], *offs)
    return bytes(body)


def table_for(name):
    files = TABLES[name]
    blobs = {f: leaf(f) for f in files}
    if len(set(blobs.values())) != 1:
        raise ValueError(f"{name}: files differ: {files}")
    t = parse(blobs[files[0]])
    for s in t["strings"]:
        s["id"] = f"{name}-{s.pop('off'):04x}"
    return {"files": files, **t}


def main():
    force, check = "--force" in sys.argv, "--check" in sys.argv
    SCRIPT.mkdir(exist_ok=True)
    bad = 0
    for name in TABLES:
        path = SCRIPT / f"{name}.json"
        if check:
            t = json.loads(path.read_text(encoding="utf-8"))
            for f in t["files"]:
                if build(t) != leaf(f):
                    print("MISMATCH", name, f)
                    bad += 1
            continue
        t = table_for(name)
        if path.exists():
            if not force:
                print("keep", path.name)
                continue
            old = {s["id"]: s for s in json.loads(path.read_text(encoding="utf-8"))["strings"]}
            for s in t["strings"]:
                s.update({k: old[s["id"]][k] for k in ("en", "notes") if s["id"] in old})
        path.write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print("wrote", path.name, len(t["strings"]), "strings")
    if check:
        print("roundtrip", "FAIL" if bad else "ok")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
