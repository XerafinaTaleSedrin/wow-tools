"""Decode a TSM group import string exactly as TSM does (GroupImport.lua _DecodeNewImport):
LibDeflate:DecodeForPrint -> raw DEFLATE decompress -> LibSerialize deserialize.
Read-only: prints what the import contains and writes a JSON summary next to the input file.

Usage: python tsm_import_decode.py path/to/import-string.txt"""
import collections
import json
import re
import struct
import sys
import zlib

ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789()"
SIX = {c: i for i, c in enumerate(ALPHA)}


def decode_for_print(s):
    s = s.strip()
    out = bytearray()
    i, n = 0, len(s)
    while i <= n - 4:
        x1, x2, x3, x4 = (SIX[c] for c in s[i:i + 4])
        cache = x1 + x2 * 64 + x3 * 4096 + x4 * 262144
        out += bytes((cache & 255, (cache >> 8) & 255, (cache >> 16) & 255))
        i += 4
    cache, bits = 0, 0
    while i < n:
        cache += SIX[s[i]] << bits
        bits += 6
        i += 1
    while bits >= 8:
        out.append(cache & 255)
        cache >>= 8
        bits -= 8
    return bytes(out)


class Reader:
    def __init__(self, data):
        self.d, self.p = data, 0
        self.strs, self.tabs = [None], [None]

    def bytes_(self, n):
        b = self.d[self.p:self.p + n]
        if len(b) < n:
            raise ValueError("read past end")
        self.p += n
        return b

    def int_(self, n):
        return int.from_bytes(self.bytes_(n), "big")

    def string(self, n):
        v = self.bytes_(n).decode("utf-8", errors="replace")
        if n > 2:
            self.strs.append(v)
        return v

    def table(self, count, t=None):
        if t is None:
            t = {}
            self.tabs.append(t)
        for _ in range(count):
            k = self.obj()
            v = self.obj()
            t[k] = v
        return t

    def array(self, count, t=None):
        if t is None:
            t = {}
            self.tabs.append(t)
        for i in range(1, count + 1):
            t[i] = self.obj()
        return t

    def mixed(self, a, m):
        t = {}
        self.tabs.append(t)
        self.array(a, t)
        self.table(m, t)
        return t

    def obj(self):
        v = self.int_(1)
        if v % 2 == 1:
            return (v - 1) // 2
        if v % 4 == 2:
            typ = (v - 2) // 4
            count = typ // 4
            typ %= 4
            if typ == 0:
                return self.string(count)
            if typ == 1:
                return self.table(count)
            if typ == 2:
                return self.array(count)
            return self.mixed(count % 4 + 1, count // 4 + 1)
        if v % 8 == 4:
            packed = self.int_(1) * 256 + v
            return -(packed - 12) // 16 if v % 16 == 12 else (packed - 4) // 16
        typ = v // 8
        R = {
            0: lambda: None,
            1: lambda: self.int_(2), 2: lambda: -self.int_(2),
            3: lambda: self.int_(3), 4: lambda: -self.int_(3),
            5: lambda: self.int_(4), 6: lambda: -self.int_(4),
            7: lambda: self.int_(7), 8: lambda: -self.int_(7),
            9: lambda: struct.unpack(">d", self.bytes_(8))[0],
            10: lambda: float(self.bytes_(self.int_(1))), 11: lambda: -float(self.bytes_(self.int_(1))),
            12: lambda: True, 13: lambda: False,
            14: lambda: self.string(self.int_(1)), 15: lambda: self.string(self.int_(2)), 16: lambda: self.string(self.int_(3)),
            17: lambda: self.table(self.int_(1)), 18: lambda: self.table(self.int_(2)), 19: lambda: self.table(self.int_(3)),
            20: lambda: self.array(self.int_(1)), 21: lambda: self.array(self.int_(2)), 22: lambda: self.array(self.int_(3)),
            23: lambda: self.mixed(self.int_(1), self.int_(1)), 24: lambda: self.mixed(self.int_(2), self.int_(2)),
            25: lambda: self.mixed(self.int_(3), self.int_(3)),
            26: lambda: self.strs[self.int_(1)], 27: lambda: self.strs[self.int_(2)], 28: lambda: self.strs[self.int_(3)],
            29: lambda: self.tabs[self.int_(1)], 30: lambda: self.tabs[self.int_(2)], 31: lambda: self.tabs[self.int_(3)],
        }
        return R[typ]()


def decode_import(s):
    raw = decode_for_print(s)
    d = zlib.decompressobj(-15)
    data = d.decompress(raw) + d.flush()
    if d.unused_data:
        raise ValueError(f"import string had {len(d.unused_data)} extra bytes")
    r = Reader(data)
    version = r.int_(1)
    values = []
    while r.p < len(data):
        values.append(r.obj())
    magic, ver, group_name, items, groups, group_ops, operations, custom = values[:8]
    return {"serializer_version": version, "magic": magic, "version": ver, "groupName": group_name,
            "items": items, "groups": groups, "groupOperations": group_ops, "operations": operations,
            "customSources": custom}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python tsm_import_decode.py IMPORT_STRING_FILE")
    path = sys.argv[1]
    s = open(path, encoding="utf-8").read().strip()
    bad = set(c for c in s if c not in SIX)
    assert not bad, f"characters TSM's decoder would reject: {sorted(bad)}"
    imp = decode_import(s)
    items = imp["items"]
    print("magic:", imp["magic"], "| version:", imp["version"], "| top group:", imp["groupName"])
    print("groups:", len(imp["groups"]), "| items:", len(items),
          "| operation types:", list(imp["operations"].keys()) if isinstance(imp["operations"], dict) else imp["operations"],
          "| custom sources:", list(imp["customSources"].keys()) if isinstance(imp["customSources"], dict) else imp["customSources"])
    per = collections.Counter(items.values())
    for g in sorted(imp["groups"], key=str):
        print(f"  {str(g).replace(chr(96), ' > '):60} {per.get(g, 0)}")
    bad_items = [k for k in items if not (isinstance(k, str) and re.match(r"^[ip]:\d+", k))]
    print("non-standard item keys:", len(bad_items), bad_items[:5])
    out = path.rsplit(".", 1)[0] + ".decoded.json"
    json.dump({"groupName": imp["groupName"], "items": items, "groups": list(imp["groups"])}, open(out, "w", encoding="utf-8"))
    print("DECODED_OK ->", out)
