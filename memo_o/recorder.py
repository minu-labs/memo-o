import logging
import queue
import threading
import time
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sounddevice as sd

from .i18n import tr
from .wavfile import CrashSafeWavWriter

PREFERRED_RATE = 16000  # Whisper 입력 샘플레이트. 음성 녹음엔 충분하고 용량도 작다.

log = logging.getLogger(__name__)
# soundcard는 루프백에서 이 플래그를 수시로 올리지만 실제 프레임 손실은 없다.
warnings.filterwarnings("ignore", message="data discontinuity in recording")


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
    devices = [InputDevice(None, tr("mic.default"))]
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


class LoopbackBuffer:
    """시스템 소리 샘플을 모아 두었다가 마이크 콜백 박자에 맞춰 꺼내 준다.

    두 장치는 클럭이 미세하게 달라 시간이 지나면 한쪽이 밀리거나 모자란다.
    지연을 목표치(target)만큼 유지하고, 너무 쌓이면 오래된 샘플을 버리고,
    바닥나면 무음으로 채운 뒤 다시 target 만큼 쌓일 때까지 기다린다.
    """

    def __init__(self, rate: int, target: float = 0.1, max_lag: float = 0.5):
        self.target = int(rate * target)
        self.max_lag = int(rate * max_lag)
        self._buf = np.zeros(0, np.float32)
        self._primed = False
        self._lock = threading.Lock()

    def push(self, samples: np.ndarray) -> None:
        with self._lock:
            buf = np.concatenate((self._buf, samples.astype(np.float32, copy=False)))
            if len(buf) > self.max_lag:
                buf = buf[-self.target:]
            self._buf = buf

    def pull(self, n: int) -> np.ndarray:
        with self._lock:
            if not self._primed:
                if len(self._buf) < self.target:
                    return np.zeros(n, np.float32)
                self._primed = True
            if len(self._buf) < n:
                out = np.concatenate((self._buf, np.zeros(n - len(self._buf), np.float32)))
                self._buf = np.zeros(0, np.float32)
                self._primed = False
                return out
            out, self._buf = self._buf[:n], self._buf[n:]
            return out


def mix(mic: np.ndarray, system: np.ndarray) -> np.ndarray:
    """int16 마이크 샘플과 float(-1~1) 시스템 소리를 더해 int16으로."""
    out = mic.astype(np.float32) + system * 32767.0
    return np.clip(out, -32768, 32767).astype(np.int16)


class SystemAudioCapture:
    """기본 출력 장치(스피커/헤드폰)로 나가는 소리를 WASAPI 루프백으로 캡처한다.

    soundcard는 COM을 쓰므로 장치 열기부터 읽기까지 전용 스레드에서 처리한다
    (Qt 메인 스레드는 이미 STA로 COM이 초기화되어 있다).
    """

    def __init__(self, rate: int):
        self.rate = rate
        self.buffer = LoopbackBuffer(rate)
        self.device_name = ""
        self.stopped_unexpectedly = False
        self._open_error: Exception | None = None
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, timeout: float = 5.0) -> None:
        self._thread = threading.Thread(target=self._run, name="memoo-loopback", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout):
            self._stop.set()
            raise TimeoutError("loopback open timed out")
        if self._open_error is not None:
            raise self._open_error

    def _run(self) -> None:
        import ctypes
        ole32 = ctypes.windll.ole32
        hr = -1
        try:
            # soundcard는 첫 import 때 그 스레드의 COM을 초기화하는데, 이미 초기화돼 있으면(S_FALSE)
            # 오류로 처리한다. 그래서 import 먼저, 이후 스레드를 위한 초기화는 그다음에 한다.
            import soundcard as sc
            hr = ole32.CoInitializeEx(None, 0)  # COINIT_MULTITHREADED
            speaker = sc.default_speaker()
            loopback = sc.get_microphone(id=str(speaker.id), include_loopback=True)
            block = self.rate // 100
            with loopback.recorder(samplerate=self.rate, channels=1, blocksize=block) as r:
                self.device_name = speaker.name
                self._ready.set()
                while not self._stop.is_set():
                    self.buffer.push(r.record(numframes=block)[:, 0])
        except Exception as e:
            if self._ready.is_set():
                log.exception("시스템 소리 캡처 중단")
                self.stopped_unexpectedly = True
            else:
                self._open_error = e
        finally:
            self._ready.set()
            if hr >= 0:
                ole32.CoUninitialize()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)


class Recorder:
    def __init__(self, path: Path, device: int | None = None, system_audio: bool = False):
        self.path = Path(path)
        self.device = device
        self.system_audio = system_audio
        self._system: SystemAudioCapture | None = None
        self.warning: str | None = None  # 녹음은 계속되지만 알려야 할 문제 (시스템 소리 실패 등)
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
        if self.system_audio:
            system = SystemAudioCapture(rate)
            try:
                system.start()
                self._system = system
            except Exception:
                log.exception("시스템 소리 캡처 시작 실패")
                system.stop()
                self.warning = tr("system.unavailable")
        self._writer = CrashSafeWavWriter(self.path, rate, channels=1)
        self._thread = threading.Thread(target=self._drain, name="memoo-wav-writer", daemon=True)
        self._thread.start()
        self._stream = stream
        self._started_at = time.monotonic()
        try:
            stream.start()
        except Exception:
            if self._system is not None:
                self._system.stop()
            raise

    def _open_stream(self) -> tuple[int, sd.InputStream]:
        kwargs = dict(device=self.device, channels=1, dtype="int16", callback=self._callback,
                      finished_callback=self._finished, blocksize=0)
        try:
            return PREFERRED_RATE, sd.InputStream(samplerate=PREFERRED_RATE, **kwargs)
        except sd.PortAudioError:
            rate = int(sd.query_devices(self.device, "input")["default_samplerate"])
            return rate, sd.InputStream(samplerate=rate, **kwargs)

    def _callback(self, indata: np.ndarray, frames, time_info, status) -> None:
        system = self._system
        if system is not None:
            if system.stopped_unexpectedly:
                self._system = None
                self.warning = tr("system.interrupted")
            else:
                indata = mix(indata[:, 0], system.buffer.pull(frames))
        self._queue.put(indata.tobytes())
        self.level = float(np.abs(indata.astype(np.int32)).max()) / 32768.0 if indata.size else 0.0

    def _finished(self) -> None:
        if self._stream is not None and not self._stopping:
            self._stopped_unexpectedly = True
            self.error = tr("mic.interrupted")

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
        if self._system is not None:
            self._system.stop()
        self._queue.put(None)
        if self._thread:
            self._thread.join(timeout=5)
        duration = 0.0
        if self._writer:
            self._writer.close()
            duration = self._writer.duration
        self._stream = None
        return duration
