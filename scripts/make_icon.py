"""앱 아이콘(memo-o.ico) 생성: 빨간 원 + 흰 점. PNG 페이로드를 담은 멀티 사이즈 ICO를 직접 기록한다."""
import struct
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter

SIZES = (16, 24, 32, 48, 64, 128, 256)
OUT = Path(__file__).resolve().parent.parent / "memo_o" / "resources" / "memo-o.ico"


def render(size: int) -> bytes:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    c = QPointF(size / 2, size / 2)
    p.setBrush(QColor("#D13438"))
    p.drawEllipse(c, size * 0.47, size * 0.47)
    p.setBrush(QColor("#FFFFFF"))
    p.drawEllipse(c, size * 0.18, size * 0.18)
    p.end()
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return bytes(ba)


def main() -> None:
    QGuiApplication([])
    pngs = [render(s) for s in SIZES]
    header = struct.pack("<HHH", 0, 1, len(SIZES))
    offset = 6 + 16 * len(SIZES)
    entries, blobs = b"", b""
    for s, png in zip(SIZES, pngs):
        dim = 0 if s >= 256 else s
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        offset += len(png)
        blobs += png
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(header + entries + blobs)
    print("saved", OUT)


if __name__ == "__main__":
    main()
