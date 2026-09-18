import os
import sys
from pathlib import Path

from . import APP_NAME


def app_dir() -> Path:
    """실행 파일(패키징 시) 또는 프로젝트 루트(개발 시)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_dir() -> Path:
    """PyInstaller 번들 리소스 위치 (onedir에서는 _internal)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", app_dir()))
    return Path(__file__).resolve().parent / "resources"


def data_dir() -> Path:
    override = os.environ.get("MEMOO_DATA_DIR")
    if override:
        base = Path(override)
    else:
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def recordings_dir() -> Path:
    d = data_dir() / "recordings"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return data_dir() / "memo-o.db"


def model_search_dirs() -> list[Path]:
    """설치 폴더에 번들된 모델 → 사용자가 추가한 모델 순으로 탐색."""
    user_models = data_dir() / "models"
    user_models.mkdir(parents=True, exist_ok=True)
    return [app_dir() / "models", user_models]
