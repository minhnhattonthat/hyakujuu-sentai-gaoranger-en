import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "debug"))
import blankcard  # noqa: E402
import warp  # noqa: E402


def test_scene_list_parses():
    scenes = warp.load_scenes()
    assert len(scenes) >= 80
    for s in scenes.values():
        if s["route"].endswith(".txt"):
            assert (ROOT / s["route"]).is_file(), s["name"]
        card = s["card"]
        if card and card != "unformatted":  # a card fixture must come from a scene that writes it
            assert Path(card).stem in scenes and not scenes[Path(card).stem]["card"], s["name"]
    assert scenes["save"]["swaps"] == [(0x5010, 0x5079), (0x5008, 0x5007)]


def test_blank_card():
    c = blankcard.blank_card()
    assert len(c) == 128 * 1024 and c[:2] == b"MC"
    for n in range(64):  # every header frame's last byte is the XOR of the other 127
        f = c[n * 128:(n + 1) * 128]
        x = 0
        for b in f[:127]:
            x ^= b
        assert f[127] == x, n
