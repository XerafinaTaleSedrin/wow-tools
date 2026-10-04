"""Test-only encoder: builds synthetic TSM import strings (the inverse of tsm_import_decode),
covering the subset of LibSerialize that group exports use. Not used by the tools themselves."""
import zlib

from tsm_import_decode import ALPHA


def _obj(v):
    if v is True:
        return bytes([12 * 8])
    if v is False:
        return bytes([13 * 8])
    if isinstance(v, int) and 0 <= v < 128:
        return bytes([v * 2 + 1])
    if isinstance(v, int) and 0 <= v < 65536:
        return bytes([1 * 8]) + v.to_bytes(2, "big")
    if isinstance(v, str):
        b = v.encode("utf-8")
        if len(b) < 16:
            return bytes([(len(b) * 4 + 0) * 4 + 2]) + b
        return bytes([14 * 8, len(b)]) + b
    if isinstance(v, dict):
        body = b"".join(_obj(k) + _obj(x) for k, x in v.items())
        if len(v) < 16:
            return bytes([(len(v) * 4 + 1) * 4 + 2]) + body
        return bytes([17 * 8, len(v)]) + body
    raise TypeError(type(v))


def encode_for_print(raw):
    out, i, n = [], 0, len(raw)
    while i <= n - 3:
        cache = raw[i] + raw[i + 1] * 256 + raw[i + 2] * 65536
        for _ in range(4):
            out.append(ALPHA[cache % 64])
            cache //= 64
        i += 3
    cache, bits = 0, 0
    while i < n:
        cache += raw[i] << bits
        bits += 8
        i += 1
    while bits > 0:
        out.append(ALPHA[cache % 64])
        cache //= 64
        bits -= 6
    return "".join(out)


def build_import(values):
    payload = bytes([1]) + b"".join(_obj(v) for v in values)
    c = zlib.compressobj(9, zlib.DEFLATED, -15)
    return encode_for_print(c.compress(payload) + c.flush())
