import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("MEMOO_DATA_DIR", str(Path(tempfile.mkdtemp(prefix="memoo-test-"))))
