"""Map the CD seeks logged by tools/lua/cdlog.lua to disc files.

    python -X utf8 tools/cdmap.py work/qa/<run>/log.txt [work/disc/lba.txt]

lba.txt is the output of tools/disc_lba.py ("lba size path" per line). Consecutive seeks inside one file are
collapsed into one line with the count.
"""
import re
import sys


def load_files(path):
    files = []
    for line in open(path, encoding="utf-8"):
        p = line.split()
        if len(p) >= 3 and p[0].isdigit():
            lba, size = int(p[0]), int(p[1])
            files.append((lba, lba + max(1, (size + 2047) // 2048), p[2]))
    return files


def name_of(files, lba):
    for lo, hi, n in files:
        if lo <= lba < hi:
            return f"{n}+{lba - lo}"
    return "?"


def main():
    log = sys.argv[1]
    files = load_files(sys.argv[2] if len(sys.argv) > 2 else "work/disc/lba.txt")
    last = None
    count = 0
    for line in open(log, encoding="utf-8", errors="replace"):
        m = re.search(r"CD (\w+) frame (\d+) lba (\d+) ra (\w+)", line)
        if not m:
            continue
        tag, frame, lba, ra = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        n = name_of(files, lba)
        f = n.split("+")[0]
        if f == last:
            count += 1
            continue
        last, count = f, 1
        print(f"{frame:7d} {tag:4s} ra {ra} lba {lba:6d} {n}")


if __name__ == "__main__":
    main()
