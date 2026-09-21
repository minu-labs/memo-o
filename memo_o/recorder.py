import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sounddevice as sd

from .wavfile import CrashSafeWavWriter

PREFERRED_RATE = 16000  # Whisper 입력 샘플레이트. 음성 녹음엔 충분하고 용량도 작다.


@dataclass(frozen=True)
class InputDevice:
    index: int | None  # None = 시스템 기본 마이크
    name: str


def _hostapi_index(name: str) -> int | None:
    for i, api in enumerate(sd.query_hostapis()):
        if api["name"] == name:
            return i
    return None


def list_input_devices() -> list[InputDevice]:
    """MME 장치로 녹음(샘플레이트/채널 변환 지원). MME는 이름이 31자로 잘려 WASAPI 이름으로 보완."""
    devices = [InputDevice(None, "기본 마이크")]
    try:
        all_devs = sd.query_devices()
    except Exception:
        return devices
    mme = _hostapi_index("MME")
    wasapi = _hostapi_index("Windows WASAPI")
    full_names = [d["name"] for d in all_devs if d["hostapi"] == wasapi and d["max_input_channels"] > 0]
    seen = set()
    for i, d in enumerate(all_devs):
        if d["max_input_channels"] <= 0:
            continue
        if mme is not None and d["hostapi"] != mme:
            continue
        name = d["name"]
        if "Sound Mapper" in name or "사운드 매퍼" in name:
            continue
        name = next((f for f in full_names if f.startswith(name)), name)
        if name in seen:
            continue
        seen.add(name)
        devices.append(InputDevice(i, name))
    return devices


class Recorder:
    def __init__(self, path: Path, device: int | None = None):
        self.path = Path(path)
        self.device = device
        self._queue: queue.Queue[bytes | None] = queue.Queue()
        self._stream: sd.InputStream | None = None
        self._writer: CrashSafeWavWriter | None = None
        self._thread: threading.Thread | None = None
        self._started_at = 0.0
        self._stopping = False
        self._stopped_unexpectedly = False
        self.error: str | None = None
        self.level = 0.0  # 최근 오디오 청크의 피크 레벨 (0~1)

    def start(self) -> None:
        rate, stream = self._open_stream()
        self._writer = CrashSafeWavWriter(self.path, rate, channels=1)
        self._thread = threading.Thread(target=self._drain, name="memoo-wav-writer", daemon=True)
        self._thread.start()
        self._stream = stream
        self._started_at = time.monotonic()
        stream.start()

    def _open_stream(self) -> tuple[int, sd.InputStream]:
        kwargs = dict(device=self.device, channels=1, dtype="int16", callback=self._callback,
                      finished_callback=self._finished, blocksize=0)
        try:
            return PREFERRED_RATE, sd.InputStream(samplerate=PREFERRED_RATE, **kwargs)
        except sd.PortAudioError:
            rate = int(sd.query_devices(self.device, "input")["default_samplerate"])
            return rate, sd.InputStream(samplerate=rate, **kwargs)

    def _callback(self, indata: np.ndarray, frames, time_info, status) -> None:
        self._queue.put(indata.tobytes())
        self.level = float(np.abs(indata).max()) / 32768.0 if indata.size else 0.0

    def _finished(self) -> None:
        if self._stream is not None and not self._stopping:
            self._stopped_unexpectedly = True
            self.error = "마이크 입력이 중단되었습니다."

    def _drain(self) -> None:
        while True:
            chunk = self._queue.get()
            if chunk is None:
                break
            self._writer.write(chunk)

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._started_at if self._stream else 0.0

    @property
    def failed(self) -> bool:
        return self._stopped_unexpectedly

    def stop(self) -> float:
        """녹음을 끝내고 실제 기록된 길이(초)를 반환."""
        self._stopping = True
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except sd.PortAudioError:
                pass
        self._queue.put(None)
        if self._thread:
            self._thread.join(timeout=5)
        duration = 0.0
        if self._writer:
            self._writer.close()
            duration = self._writer.duration
        self._stream = None
        return duration
