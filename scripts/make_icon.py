"""앱 아이콘(memo-o.ico) 생성: 둥근 사각 배지 + 흰 사운드바. PNG 페이로드를 담은 멀티 사이즈 ICO를 직접 기록한다."""
import struct
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QGuiApplication, QImage, QLinearGradient, QPainter

SIZES = (16, 24, 32, 48, 64, 128, 256)
OUT_PATHS = (
    Path(__file__).resolve().parent.parent / "memo_o" / "resources" / "memo-o.ico",
    Path(__file__).resolve().parent.parent / "web" / "public" / "favicon.ico",
)


def render(size: int) -> bytes:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)

    # 배지: 완전한 원 대신 둥근 사각형 + 그라데이션으로 입체감을 준다.
    margin = size * 0.04
    rect = QRectF(margin, margin, size - margin * 2, size - margin * 2)
    grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    grad.setColorAt(0.0, QColor("#E2555A"))
    grad.setColorAt(1.0, QColor("#B92B2E"))
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(rect, size * 0.24, size * 0.24)

    # 사운드바 3개 (가운데가 가장 김)
    p.setBrush(QColor("#FFFFFF"))
    bar_w = size * 0.115
    gap = size * 0.08
    heights = (size * 0.26, size * 0.46, size * 0.34)
    total_w = bar_w * len(heights) + gap * (len(heights) - 1)
    x = size / 2 - total_w / 2
    cy = size / 2
    for h in heights:
        bar = QRectF(x, cy - h / 2, bar_w, h)
        p.drawRoundedRect(bar, bar_w / 2, bar_w / 2)
        x += bar_w + gap

    p.end()
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice

    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return bytes(ba)


def build_ico(pngs: list[bytes]) -> bytes:
    header = struct.pack("<HHH", 0, 1, len(SIZES))
    offset = 6 + 16 * len(SIZES)
    entries, blobs = b"", b""
    for s, png in zip(SIZES, pngs):
        dim = 0 if s >= 256 else s
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        offset += len(png)
        blobs += png
    return header + entries + blobs


def main() -> None:
    QGuiApplication([])
    pngs = [render(s) for s in SIZES]
    ico = build_ico(pngs)
    for out in OUT_PATHS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(ico)
        print("saved", out)


if __name__ == "__main__":
    main()
