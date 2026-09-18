"""개발/빌드용: faster-whisper 모델을 models/<size> 로 내려받는다 (앱 자체는 네트워크를 쓰지 않음)."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

from huggingface_hub import snapshot_download

size = sys.argv[1] if len(sys.argv) > 1 else "small"
dest = Path(__file__).resolve().parent.parent / "models" / size
# WSL 공유 경로에서는 파일 잠금이 안 되므로 로컬 임시 폴더에 받은 뒤 복사
tmp = Path(tempfile.gettempdir()) / "memoo-models" / size
snapshot_download(
    repo_id=f"Systran/faster-whisper-{size}",
    local_dir=tmp,
    allow_patterns=["config.json", "model.bin", "tokenizer.json", "vocabulary.*", "preprocessor_config.json"],
)
dest.mkdir(parents=True, exist_ok=True)
for p in tmp.iterdir():
    if p.is_file():
        shutil.copy2(p, dest / p.name)
        print(f"  {p.name}  {p.stat().st_size/1e6:.1f} MB")
print("saved:", dest)
