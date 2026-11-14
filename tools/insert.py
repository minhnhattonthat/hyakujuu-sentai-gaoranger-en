"""insert.py: write the English text tables and the English font into the PAC files (build.py calls it).

Every script/*.json table goes to each file in its "files" (leaf paths as in extract.py: slot numbers, lzs blocks
decoded on the way). Each string uses `en` if set, else its `jp` bytes unchanged. The font TIM (19 identical copies,
FONT_LEAVES) gets the English cells from font.py. Changed PACs are written to OVERLAY/DATA/.

    insert(overlay, marker=False)  -> list of PAC names written
marker=True replaces every string that has Japanese text with "[id] The quick brown fox..." (phase 5 marker build).
"""
import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import font  # noqa: E402
import pac  # noqa: E402
from tbl import Table  # noqa: E402

DATA = ROOT / "work" / "disc" / "tree" / "DATA"
SCRIPT = ROOT / "script"
EN = None  # Table, loaded on first use (font.py writes tbl/en.tbl)
FONT_LEAVES = ["CARDMS.PAC/1", "O_START.PAC/8", "Y_TITLE.PAC/12_5", "Y_EDSAVE.PAC/14_16_7", "Y_LOAD.PAC/13_16_7",
               "Y_OPTION.PAC/13_16_7", "Y_SAVE.PAC/14_16_7"] + \
              [f"DE_ST0{i}.PAC/9_7" for i in range(1, 6)] + [f"DS_ST0{i}.PAC/9_7" for i in range(1, 8)]
JP_TEXT = re.compile(r"[぀-ヿ一-鿿]")
PANGRAM = "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs. "
MARKER_LINE = 40  # characters per marker line (story box: 48 columns)
# Decoded table sizes a runtime trace showed safe (no decode lands in the grown tail; docs/re/pac.md §Decode targets,
# lzsmap.TRACE_SCENES). A release build fails if a table grows past this (a table not listed: past its jp size);
# re-run the trace on the new build, then raise the number. Marker and --qa builds are QA-only and not capped.
TRACED = {"card": 2128, "save": 1232, "load": 798, "option": 452, "ds01": 448, "ds02": 346, "ds03": 352,
          "ds04": 318, "ds05": 320, "ds06": 354, "ds07": 330}


def marker(s):
    """Marker text for string s: leading control codes kept, one marker line per Japanese line."""
    lead = re.match(r"(\{col:[0-9A-F]{2}\})*", s["jp"])[0]
    lines = s["jp"].split("{n}")
    out = []
    for i, _ in enumerate(lines):
        head = f"[{s['id']}] " if i == 0 else f"{i + 1}: "
        out.append((head + PANGRAM)[:MARKER_LINE].rstrip())
    return lead + "{n}".join(out)


def text_for(s, marker_mode, qa=None):
    """The text string s gets in the build (None: keep its jp bytes)."""
    text = marker(s) if marker_mode and JP_TEXT.search(s["jp"]) else s.get("en")
    return (qa or {}).get(s["id"], text)


def encode_table(t, marker_mode, qa=None):
    """Table dict -> bytes. Strings without `en` (and non-text strings in marker mode) keep their jp bytes.
    qa: {id: text} overrides (stress lines for the width gate)."""
    global EN
    EN = EN or Table.load(ROOT / "tbl" / "en.tbl")
    body = bytearray(bytes(4 + 2 * t["count"] + t["lead"]))
    offs = [0] * t["count"]
    for s in t["strings"]:
        for i in s["slots"]:
            offs[i] = len(body)
        text = text_for(s, marker_mode, qa)
        body += EN.encode(text + "{end}") if text else extract.TBL.encode(s["jp"] + "{end}")
        body += bytes(s["pad"] + (len(body) + s["pad"]) % 2)
    for i in t["end_slots"]:
        offs[i] = len(body)
    struct.pack_into(f"<HH{t['count']}H", body, 0, t["a"], t["count"], *offs)
    return bytes(body)


def set_leaf(node, parts, data):
    """Replace the leaf at slot path `parts` under node; lzs blocks on the way are decoded into a "tree"."""
    if not parts:
        if node["kind"] == "lzs":
            return {**node, "payload": data, "pad_to": len(node["raw"])}
        return {"kind": "raw", "raw": data + bytes(max(0, len(node["raw"]) - len(data)))}
    if node["kind"] == "lzs":
        if "tree" not in node:
            node["tree"] = pac.parse(pac.lzs_decode(node["raw"], 0)[0])
        node["tree"] = set_leaf(node["tree"], parts, data)
        return node
    assert node["kind"] == "add", node["kind"]
    node["slots"][parts[0]] = set_leaf(node["slots"][parts[0]], parts[1:], data)
    return node


def finish(node):
    """Turn decoded lzs trees back into payload bytes, bottom up."""
    if node["kind"] == "add":
        for c in node["slots"].values():
            finish(c)
    elif "tree" in node:
        finish(node["tree"])
        node["payload"] = pac.build(node.pop("tree"))
        node["pad_to"] = len(node["raw"])


def insert(overlay, marker=False, qa=None):
    edits = defaultdict(list)  # PAC name -> [(slot path, bytes)]
    ids = set()
    for path in sorted(SCRIPT.glob("*.json")):
        t = json.loads(path.read_text(encoding="utf-8"))
        ids |= {s["id"] for s in t["strings"]}
        blob = encode_table(t, marker, qa)
        cap = TRACED.get(path.stem) or len(extract.leaf(t["files"][0]))
        if not marker and not qa and len(blob) > cap:
            raise SystemExit(f"{path.stem}: table is {len(blob)} bytes, only {cap} traced safe at runtime: re-run "
                             "the lzslog trace (tools/lzsmap.py docstring) and raise insert.TRACED")
        for f in t["files"]:
            name, leaf = f.split("/")
            edits[name].append(([int(p) for p in leaf.split("_")], blob))
    if set(qa or {}) - ids:
        raise SystemExit(f"--qa ids not in script/: {sorted(set(qa) - ids)}")
    tim = font.patch_tim(extract.leaf(FONT_LEAVES[0]))
    for f in FONT_LEAVES:
        assert extract.leaf(f) == extract.leaf(FONT_LEAVES[0]), f
        name, leaf = f.split("/")
        edits[name].append(([int(p) for p in leaf.split("_")], tim))
    out = Path(overlay) / "DATA"
    out.mkdir(parents=True, exist_ok=True)
    for name, ed in sorted(edits.items()):
        node = pac.parse((DATA / name).read_bytes())
        for parts, data in ed:
            node = set_leaf(node, parts, data)
        finish(node)
        b = pac.build(node)
        (out / name).write_bytes(b)
        for f, data in ((f"{name}/{'_'.join(map(str, p))}", d) for p, d in ed):
            got = leaf_of(b, f.split("/")[1])  # the written PAC gives back every leaf (raw ones zero-padded)
            assert got[:len(data)] == data and not any(got[len(data):]), f
        check_offsets(name, b)
    return sorted(edits)


def check_offsets(name, built):
    """No block in the built PAC starts earlier than in the original: the game decodes lzs blocks in a way that
    broke when a block moved earlier (DE_ST01: the English font packed smaller, the next TIMs moved up by 0x2e8 and
    the ending's cloud picture lost its colours; moving later is fine, docs/re/pac.md)."""
    orig = (DATA / name).read_bytes()
    old = {p: o for p, o, s, k in pac.walk(orig, 0, len(orig))}
    for p, o, s, k in pac.walk(built, 0, len(built)):
        if p in old and o < old[p]:
            raise SystemExit(f"{name}/{'_'.join(map(str, p))} moved earlier: {old[p]:#x} -> {o:#x}")


def leaf_of(d, path):
    for part in path.split("_"):
        entries = {i: (o, s) for i, o, s in pac.add_entries(d, 0)}
        o, s = entries[int(part)]
        d = pac.lzs_decode(d, o)[0] if pac.kind(d, o) == "lzs" else d[o:o + s]
    return d
