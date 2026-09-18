"""models/<size> → dist/memo-o/models/<size> 복사 (해시 검증 + 재시도).

\\\\wsl.localhost 네트워크 경로 간 대용량 파일을 robocopy/Copy-Item으로 복사하면
파일 크기는 같지만 내용이 손상되는 경우가 있어, 표준 파이썬 청크 복사 후
SHA-256을 비교해 다를 경우 재시도한다.

python -m scripts.copy_model [size]
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNK = 4 << 20


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_chunked(src: Path, dst: Path) -> None:
    with open(src, "rb") as fs, open(dst, "wb") as fd:
        while True:
            buf = fs.read(CHUNK)
            if not buf:
                break
            fd.write(buf)
        fd.flush()


def main() -> None:
    size = sys.argv[1] if len(sys.argv) > 1 else "small"
    src = ROOT / "models" / size
    dest = ROOT / "dist" / "memo-o" / "models" / size
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.iterdir()):
        if not f.is_file():
            continue
        d = dest / f.name
        src_hash = sha256(f)
        if d.exists() and d.stat().st_size == f.stat().st_size and sha256(d) == src_hash:
            print(f"skip {f.name} (이미 동일)")
            continue
        for attempt in range(1, 6):
            copy_chunked(f, d)
            if sha256(d) == src_hash:
                print(f"ok   {f.name}  ({d.stat().st_size / 1e6:.1f} MB, 시도 {attempt})")
                break
            print(f"retry {attempt}: {f.name} 체크섬 불일치, 다시 복사")
        else:
            raise SystemExit(f"복사 실패(체크섬 불일치 반복): {f.name}")


if __name__ == "__main__":
    main()
