import wave
from datetime import datetime

import numpy as np
import pytest

from memo_o import db as dbm
from memo_o.db import Database, Segment
from memo_o.export import fmt_clock, fmt_hms, to_srt, to_txt
from memo_o.wavfile import CrashSafeWavWriter, repair


def _frames(path):
    with wave.open(str(path)) as w:
        return w.getnframes(), w.getframerate(), w.getnchannels()


def test_wav_writer_roundtrip(tmp_path):
    p = tmp_path / "a.wav"
    w = CrashSafeWavWriter(p, 16000)
    w.write(b"\x01\x00" * 16000)
    w.close()
    assert _frames(p) == (16000, 16000, 1)
    assert w.duration == pytest.approx(1.0)


def test_wav_header_is_synced_while_recording(tmp_path):
    p = tmp_path / "b.wav"
    w = CrashSafeWavWriter(p, 16000, sync_interval=0)
    w.write(b"\x00\x00" * 8000)
    # 닫지 않은 상태(강제 종료 상황)에서도 헤더가 유효해야 한다
    assert _frames(p)[0] == 8000
    w._f.close()


def test_repair_after_crash(tmp_path):
    p = tmp_path / "c.wav"
    w = CrashSafeWavWriter(p, 16000, sync_interval=3600)
    w.write(b"\x00\x00" * 16000)
    w._f.flush()
    w._f.close()  # sync 없이 종료 → 헤더상 길이 0
    assert _frames(p)[0] == 0
    assert repair(p) == pytest.approx(1.0)
    assert _frames(p)[0] == 16000


def test_repair_drops_partial_frame(tmp_path):
    p = tmp_path / "d.wav"
    w = CrashSafeWavWriter(p, 16000)
    w.write(b"\x00\x00" * 10)
    w.close()
    with open(p, "ab") as f:
        f.write(b"\x00")
    repair(p)
    assert _frames(p)[0] == 10


@pytest.fixture
def db(tmp_path):
    d = Database(tmp_path / "t.db")
    yield d
    d.close()


def test_db_crud_and_search(db, tmp_path):
    now = datetime(2026, 9, 18, 10, 0)
    a = db.create_recording("아이디어 메모", tmp_path / "a.wav", now)
    b = db.create_recording("강의 노트", tmp_path / "b.wav", now.replace(hour=11))
    assert db.get(a).status == dbm.RECORDING

    db.update(a, duration=12.5, status=dbm.PENDING)
    db.save_transcript(a, [Segment(0, 1.5, "100% 확신합니다"), Segment(1.5, 3, "다음 안건")], "small")
    rec = db.get(a)
    assert rec.status == dbm.DONE and rec.model == "small"
    assert rec.transcript == "100% 확신합니다\n다음 안건"
    assert [s.text for s in db.segments(a)] == ["100% 확신합니다", "다음 안건"]

    assert [r.id for r in db.list()] == [b, a]  # 최신순
    assert [r.id for r in db.list("강의")] == [b]
    assert [r.id for r in db.list("안건")] == [a]
    assert db.count("100%") == 1
    assert db.count("0%확") == 0  # %는 와일드카드가 아닌 문자로 취급
    assert db.count() == 2
    assert db.ids_with_status(dbm.RECORDING) == [b]

    db.delete(a)
    assert db.get(a) is None and db.segments(a) == []


def test_db_update_rejects_unknown_field(db, tmp_path):
    rid = db.create_recording("x", tmp_path / "x.wav", datetime.now())
    with pytest.raises(ValueError):
        db.update(rid, file_path="evil")


def test_settings(db):
    assert db.get_setting("model", "small") == "small"
    db.set_setting("model", "medium")
    db.set_setting("model", "small")
    assert db.get_setting("model") == "small"


def test_formatting():
    assert fmt_clock(65) == "01:05"
    assert fmt_clock(3725) == "1:02:05"
    assert fmt_hms(3725) == "01:02:05"


def test_export(tmp_path):
    rec = dbm.Recording(1, "강의 노트", datetime(2026, 9, 17, 9, 30), 64, tmp_path / "a.wav",
                        dbm.DONE, "small", None, "")
    segs = [Segment(0, 2.345, "안녕하세요"), Segment(62, 64, "끝")]
    txt = to_txt(rec, segs)
    assert "강의 노트" in txt and "[00:00] 안녕하세요" in txt and "[01:02] 끝" in txt
    srt = to_srt(segs)
    assert srt.startswith("1\n00:00:00,000 --> 00:00:02,345\n안녕하세요\n")
    assert "2\n00:01:02,000 --> 00:01:04,000\n끝" in srt


def test_service_recovers_crashed_recording(db, tmp_path):
    from memo_o.transcription import TranscriptionService

    wav = tmp_path / "crash.wav"
    w = CrashSafeWavWriter(wav, 16000, sync_interval=3600)
    w.write(b"\x00\x00" * 32000)
    w._f.flush()
    w._f.close()  # 헤더 갱신 전에 프로세스가 죽은 상황
    crashed = db.create_recording("크래시", wav, datetime.now())
    missing = db.create_recording("없음", tmp_path / "nope.wav", datetime.now())

    TranscriptionService(db).recover()

    rec = db.get(crashed)
    assert rec.status == dbm.PENDING and rec.duration == pytest.approx(2.0)
    assert _frames(wav)[0] == 32000
    assert db.get(missing).status == dbm.ERROR


def _write_wav(path, seconds=1.0, rate=16000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))


def test_import_audio_copies_and_queues(db, tmp_path):
    from memo_o.importer import import_audio

    src = tmp_path / "강의 노트.WAV"
    _write_wav(src, 1.5)
    now = datetime(2026, 10, 1, 9, 0)
    a = import_audio(db, src, now)
    b = import_audio(db, src, now)  # 같은 시각에 여러 개 가져와도 파일명이 겹치지 않는다

    rec = db.get(a)
    assert rec.title == "강의 노트" and rec.status == dbm.PENDING
    assert rec.duration == pytest.approx(1.5)
    assert rec.file_path.suffix == ".wav" and rec.file_path.read_bytes() == src.read_bytes()
    assert rec.file_path != src and rec.file_path != db.get(b).file_path
    assert src.exists()  # 원본은 그대로


def test_import_audio_rejects_bad_files(db, tmp_path):
    from memo_o.importer import import_audio
    from memo_o.paths import recordings_dir

    before = set(recordings_dir().iterdir())
    txt = tmp_path / "memo.txt"
    txt.write_text("hello")
    fake = tmp_path / "broken.mp3"
    fake.write_bytes(b"not audio at all" * 10)
    for p in (txt, fake):
        with pytest.raises(ValueError):
            import_audio(db, p)
    assert db.count() == 0
    assert set(recordings_dir().iterdir()) == before  # 실패한 파일은 복사되지 않는다


def test_loopback_buffer_waits_until_primed():
    from memo_o.recorder import LoopbackBuffer
    b = LoopbackBuffer(1000, target=0.1, max_lag=0.5)  # target 100, max 500 샘플
    b.push(np.ones(50, np.float32))
    assert not b.pull(10).any()  # 목표 지연만큼 쌓이기 전엔 무음
    b.push(np.ones(50, np.float32))
    assert b.pull(10).all()


def test_loopback_buffer_underrun_pads_and_reprimes():
    from memo_o.recorder import LoopbackBuffer
    b = LoopbackBuffer(1000, target=0.1, max_lag=0.5)
    b.push(np.ones(100, np.float32))
    out = b.pull(150)
    assert out[:100].all() and not out[100:].any()
    b.push(np.ones(50, np.float32))
    assert not b.pull(10).any()  # 다시 target 까지 기다린다


def test_loopback_buffer_overrun_drops_to_target():
    from memo_o.recorder import LoopbackBuffer
    b = LoopbackBuffer(1000, target=0.1, max_lag=0.5)
    b.push(np.zeros(500, np.float32))
    b.push(np.arange(1, 11, dtype=np.float32))  # 510 > 500 → 최근 100개만 남김
    out = b.pull(100)
    assert out[-10:].tolist() == list(range(1, 11))


def test_mix_clips_to_int16():
    from memo_o.recorder import mix
    mic = np.array([30000, -30000, 100], np.int16)
    out = mix(mic, np.array([0.5, -0.5, 0.0], np.float32))
    assert out.dtype == np.int16
    assert out.tolist() == [32767, -32768, 100]
