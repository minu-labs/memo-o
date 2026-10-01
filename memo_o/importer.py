"""PC에 있는 음성/영상 파일을 녹음 목록으로 가져온다 (원본은 그대로 두고 데이터 폴더로 복사)."""
import shutil
from datetime import datetime
from pathlib import Path

from . import db as dbm
from .db import Database
from .i18n import tr
from .paths import recordings_dir

# faster-whisper가 PyAV(FFmpeg)로 디코딩하므로 영상 파일의 소리도 변환할 수 있다.
AUDIO_EXTS = (
    ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma", ".amr", ".3gp",
    ".mp4", ".mov", ".mkv", ".avi", ".webm",
)


def is_supported(path: Path) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTS


def probe_duration(path: Path) -> float:
    """오디오 길이(초). 소리가 없거나 읽을 수 없는 파일이면 ValueError."""
    import av

    try:
        with av.open(str(path), metadata_errors="ignore") as c:
            streams = c.streams.audio
            if not streams:
                raise ValueError(tr("import.no_audio"))
            s = streams[0]
            if s.duration and s.time_base:
                return float(s.duration * s.time_base)
            if c.duration:
                return c.duration / av.time_base
            # 길이 정보가 없는 파일은 패킷을 끝까지 읽어 계산한다
            end = 0.0
            for p in c.demux(s):
                if p.pts is not None and p.duration:
                    end = max(end, float((p.pts + p.duration) * s.time_base))
            return end
    except av.FFmpegError as e:
        raise ValueError(tr("import.unreadable")) from e


def _target_path(src: Path, now: datetime) -> Path:
    base = f"{now:%Y%m%d_%H%M%S}"
    ext = src.suffix.lower()
    path = recordings_dir() / f"{base}{ext}"
    n = 1
    while path.exists():
        path = recordings_dir() / f"{base}_{n}{ext}"
        n += 1
    return path


def import_audio(db: Database, src: Path, now: datetime | None = None) -> int:
    """파일을 복사해 '변환 대기'로 등록하고 녹음 id를 반환한다. 대기열 추가는 호출자가 한다."""
    src = Path(src)
    if not is_supported(src):
        raise ValueError(tr("import.unsupported"))
    duration = probe_duration(src)
    now = now or datetime.now()
    dst = _target_path(src, now)
    try:
        shutil.copyfile(src, dst)
    except BaseException:
        dst.unlink(missing_ok=True)
        raise
    return db.create_recording(src.stem.strip()[:100] or src.name, dst, now,
                               duration=duration, status=dbm.PENDING)
