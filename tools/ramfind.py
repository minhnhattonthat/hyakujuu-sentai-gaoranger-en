"""ramfind.py RAM.bin: which disc files sit raw in a RAM dump (samples 32-byte chunks of each PAC/PRG/EXE).
Prints file, (file offset, RAM address) pairs. Base address = RAM address - file offset."""
import sys, glob, os
ram = open(sys.argv[1], 'rb').read()
for f in sorted(glob.glob('work/disc/tree/DATA/*.PAC')) + sorted(glob.glob('work/disc/tree/DATA/*.PRG')) + ['work/disc/tree/SLPS_033.53']:
    d = open(f, 'rb').read()
    if len(d) < 0x200:
        continue
    hits = []
    for o in range(0x40, len(d) - 32, max(0x400, len(d) // 64)):
        c = d[o:o + 32]
        if c.count(0) > 20:
            continue
        i = ram.find(c)
        if i >= 0:
            hits.append((o, i))
    if hits:
        print(os.path.basename(f), [(hex(o), hex(0x80000000 + i)) for o, i in hits[:4]], len(hits))
