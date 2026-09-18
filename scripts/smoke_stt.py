"""STT 스모크 테스트: python -m scripts.smoke_stt <wav> [size]"""
import sys
import time

from memo_o.export import fmt_clock
from memo_o.stt import Transcriber

path = sys.argv[1]
size = sys.argv[2] if len(sys.argv) > 2 else "small"
t = Transcriber()
t0 = time.perf_counter()
t._load(size)
t1 = time.perf_counter()
segs = t.transcribe(path, size, on_progress=lambda p: print(f"  progress {p:.0%}"))
t2 = time.perf_counter()
print(f"device={t.device} load={t1-t0:.1f}s transcribe={t2-t1:.1f}s")
for s in segs:
    print(f"[{fmt_clock(s.start)}] {s.text}")
