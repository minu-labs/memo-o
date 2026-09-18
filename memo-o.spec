# PyInstaller 빌드 설정: pyinstaller memo-o.spec
# onedir 방식: 실행 시 압축 해제가 없어 시작이 빠르고, LGPL(Qt) 라이브러리 교체가 가능하다.
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = [
    ("memo_o/resources/memo-o.ico", "."),
    ("memo_o/resources/THIRD_PARTY_NOTICES.txt", "."),
]
datas += collect_data_files("faster_whisper")  # Silero VAD onnx 모델
binaries = collect_dynamic_libs("ctranslate2")

a = Analysis(
    ["run_memo_o.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=["PySide6.QtMultimedia"],
    excludes=[
        "tkinter", "matplotlib", "pytest", "IPython", "pandas", "scipy",
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore",
        "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtPdf", "PySide6.QtCharts",
        "PySide6.QtDataVisualization", "PySide6.QtBluetooth", "PySide6.QtPositioning",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="memo-o",
    icon="memo_o/resources/memo-o.ico",
    version="version_info.txt",
    console=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="memo-o")
