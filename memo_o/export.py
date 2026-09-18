from .db import Recording, Segment


def fmt_clock(seconds: float) -> str:
    """mm:ss, 1시간 이상이면 h:mm:ss."""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def fmt_hms(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def _srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_txt(rec: Recording, segments: list[Segment], with_timestamps: bool = True) -> str:
    header = f"{rec.title}\n{rec.created_at:%Y-%m-%d %H:%M} · {fmt_clock(rec.duration)}\n\n"
    if with_timestamps:
        body = "\n".join(f"[{fmt_clock(s.start)}] {s.text}" for s in segments)
    else:
        body = "\n".join(s.text for s in segments)
    return header + body + "\n"


def to_srt(segments: list[Segment]) -> str:
    blocks = [
        f"{i}\n{_srt_time(s.start)} --> {_srt_time(s.end)}\n{s.text}\n"
        for i, s in enumerate(segments, 1)
    ]
    return "\n".join(blocks)
