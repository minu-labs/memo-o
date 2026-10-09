"""빌드용: CTranslate2 Whisper 모델(model.bin)의 가중치를 int8로 다시 저장해 용량을 절반으로 줄인다.

python -m scripts.quantize_model models/small models/small-int8  (build.ps1 이 자동 실행)

ct2-transformers-converter --quantization int8 과 같은 방식(행별 스케일, 127/max|w|)으로
양자화 대상(LinearSpec/Conv1DSpec/EmbeddingsSpec의 weight)만 바꾸고 나머지 변수는 그대로 둔다.
CPU에서는 어차피 int8로 연산하므로 결과가 사실상 같고, GPU에서는 불러올 때 float16으로 변환된다.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

import numpy as np
from ctranslate2.specs import model_spec
from ctranslate2.specs.whisper_spec import WhisperSpec

DTYPES = ("float32", "int8", "int16", "int32", "float16", "bfloat16")  # include/ctranslate2/types.h 순서
NP_DTYPES = {"float32": np.float32, "int8": np.int8, "int16": np.int16, "int32": np.int32, "float16": np.float16}


def _read_string(f) -> str:
    n = struct.unpack("H", f.read(2))[0]
    return f.read(n)[:-1].decode("utf-8")


def _write_string(f, s: str) -> None:
    b = s.encode("utf-8")
    f.write(struct.pack("H", len(b) + 1))
    f.write(b + b"\0")


def read_model(path: Path):
    with open(path, "rb", buffering=64 << 20) as f:
        version = struct.unpack("I", f.read(4))[0]
        if version != model_spec.CURRENT_BINARY_VERSION:
            raise ValueError(f"지원하지 않는 model.bin 버전: {version}")
        name = _read_string(f)
        revision = struct.unpack("I", f.read(4))[0]
        variables = {}
        for _ in range(struct.unpack("I", f.read(4))[0]):
            vname = _read_string(f)
            ndims = struct.unpack("B", f.read(1))[0]
            shape = struct.unpack(f"{ndims}I", f.read(4 * ndims)) if ndims else ()
            dtype = DTYPES[struct.unpack("B", f.read(1))[0]]
            nbytes = struct.unpack("I", f.read(4))[0]
            data = f.read(nbytes)
            variables[vname] = np.frombuffer(data, NP_DTYPES[dtype]).reshape(shape)
        aliases = [(_read_string(f), _read_string(f)) for _ in range(struct.unpack("I", f.read(4))[0])]
    return name, revision, variables, aliases


def write_model(path: Path, name: str, revision: int, variables: dict, aliases: list) -> None:
    with open(path, "wb", buffering=64 << 20) as f:  # WSL 공유 경로에선 작은 쓰기가 매우 느리다
        f.write(struct.pack("I", model_spec.CURRENT_BINARY_VERSION))
        _write_string(f, name)
        f.write(struct.pack("I", revision))
        f.write(struct.pack("I", len(variables)))
        for vname, value in sorted(variables.items()):
            _write_string(f, vname)
            f.write(struct.pack("B", value.ndim))
            for dim in value.shape:
                f.write(struct.pack("I", dim))
            f.write(struct.pack("B", DTYPES.index(value.dtype.name)))
            data = np.ascontiguousarray(value).tobytes()
            f.write(struct.pack("I", len(data)))
            f.write(data)
        f.write(struct.pack("I", len(aliases)))
        for alias, target in aliases:
            _write_string(f, alias)
            _write_string(f, target)


def quantize_int8(value: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """ctranslate2.specs.model_spec.LayerSpec._quantize 의 int8 경로와 같은 계산."""
    w = value.astype(np.float32)
    old_shape = w.shape if w.ndim == 3 else None
    if old_shape:
        w = w.reshape(w.shape[0], -1)
    amax = np.amax(np.absolute(w), axis=1)
    amax[amax == 0] = 127.0
    scale = (127.0 / amax).astype(np.float32)
    q = np.rint(w * np.expand_dims(scale, 1)).astype(np.int8)
    if old_shape:
        q = q.reshape(old_shape)
    return q, scale


def _count_layers(variables: dict, prefix: str) -> int:
    return len({k.split("/")[1] for k in variables if k.startswith(prefix + "/layer_")})


def main(src: Path, dst: Path) -> None:
    name, revision, variables, aliases = read_model(src / "model.bin")
    if name != "WhisperSpec":
        raise ValueError(f"Whisper 모델이 아님: {name}")
    if any(v.dtype == np.int8 and k.endswith("/weight") for k, v in variables.items()):
        raise ValueError("이미 int8로 양자화된 모델")

    # 각 변수가 양자화 대상인지(스펙에 <이름>_scale 속성이 있는지)는 실제 WhisperSpec 구조로 판단한다.
    heads = 1  # 레이어 구조만 필요하므로 헤드 수는 무관
    spec = WhisperSpec(_count_layers(variables, "encoder"), heads, _count_layers(variables, "decoder"), heads)
    out = {}
    n_quantized = 0
    for vname, value in variables.items():
        scope, attr = model_spec._parent_scope(vname)
        try:
            layer = model_spec.index_spec(spec, scope)
        except (AttributeError, IndexError, ValueError):
            layer = None
        if layer is not None and hasattr(layer, f"{attr}_scale") and value.ndim > 0 \
                and value.dtype in (np.float16, np.float32):
            q, scale = quantize_int8(value)
            out[vname] = q
            out[model_spec._join_scope(scope, f"{attr}_scale")] = scale
            n_quantized += 1
        else:
            out[vname] = value

    dst.mkdir(parents=True, exist_ok=True)
    write_model(dst / "model.bin", name, revision, out, aliases)
    for p in src.iterdir():
        if p.is_file() and p.name != "model.bin":
            shutil.copy2(p, dst / p.name)
    print(f"양자화 {n_quantized}개 변수, {(src / 'model.bin').stat().st_size / 1e6:.0f}MB → "
          f"{(dst / 'model.bin').stat().st_size / 1e6:.0f}MB: {dst}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
