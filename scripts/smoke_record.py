"""마이크 3초 녹음 스모크 테스트."""
import time
from pathlib import Path

import numpy as np

from memo_o.recorder import Recorder, list_input_devices

for d in list_input_devices():
    print("device:", d.index, d.name.encode("utf-8", "replace").decode("utf-8"))
out = Path("samples/mic_test.wav")
r = Recorder(out)
r.start()
time.sleep(3)
dur = r.stop()
import wave
with wave.open(str(out)) as w:
    data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    print("rate", w.getframerate(), "ch", w.getnchannels(), "frames", w.getnframes())
print(f"duration={dur:.2f}s peak={np.abs(data).max() if data.size else 0} failed={r.failed}")
