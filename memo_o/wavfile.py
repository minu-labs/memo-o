"""강제 종료되어도 그때까지의 녹음이 재생 가능하도록 헤더를 주기적으로 갱신하는 WAV 기록기."""
import struct
import time
from pathlib import Path

HEADER_SIZE = 44


def _header(sample_rate: int, channels: int, sampwidth: int, data_bytes: int) -> bytes:
    block_align = channels * sampwidth
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_bytes, b"WAVE",
        b"fmt ", 16, 1, channels, sample_rate, sample_rate * block_align, block_align, sampwidth * 8,
        b"data", data_bytes,
    )


class CrashSafeWavWriter:
    def __init__(self, path: Path, sample_rate: int, channels: int = 1, sampwidth: int = 2,
                 sync_interval: float = 1.0):
        self.path = Path(path)
        self.sample_rate = sample_rate
        self.channels = channels
        self.sampwidth = sampwidth
        self.sync_interval = sync_interval
        self.data_bytes = 0
        self._f = open(self.path, "wb")
        self._f.write(_header(sample_rate, channels, sampwidth, 0))
        self._last_sync = time.monotonic()

    def write(self, pcm: bytes) -> None:
        self._f.write(pcm)
        self.data_bytes += len(pcm)
        if time.monotonic() - self._last_sync >= self.sync_interval:
            self.sync()

    def sync(self) -> None:
        pos = self._f.tell()
        self._f.seek(0)
        self._f.write(_header(self.sample_rate, self.channels, self.sampwidth, self.data_bytes))
        self._f.seek(pos)
        self._f.flush()
        self._last_sync = time.monotonic()

    @property
    def duration(self) -> float:
        return self.data_bytes / (self.sample_rate * self.channels * self.sampwidth)

    def close(self) -> None:
        if self._f.closed:
            return
        self.sync()
        self._f.close()


def repair(path: Path) -> float:
    """헤더의 길이 정보를 실제 파일 크기에 맞춘다. 복구된 길이(초)를 반환."""
    path = Path(path)
    size = path.stat().st_size
    if size < HEADER_SIZE:
        return 0.0
    with open(path, "r+b") as f:
        head = f.read(HEADER_SIZE)
        if head[:4] != b"RIFF" or head[8:12] != b"WAVE" or head[36:40] != b"data":
            raise ValueError(f"MemoO 형식의 WAV가 아님: {path}")
        channels, sample_rate = struct.unpack("<HI", head[22:28])
        sampwidth = struct.unpack("<H", head[34:36])[0] // 8
        block_align = channels * sampwidth
        data_bytes = (size - HEADER_SIZE) // block_align * block_align
        f.truncate(HEADER_SIZE + data_bytes)
        f.seek(0)
        f.write(_header(sample_rate, channels, sampwidth, data_bytes))
    return data_bytes / (sample_rate * block_align)
