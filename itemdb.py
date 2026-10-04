"""Decode TSMItemInfoDB records, following TSM's ItemInfoSerializer.lua exactly."""
from svparse import load

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
DEC = {c: i for i, c in enumerate(ALPHABET)}
NIL = ALPHABET[63]
REC = 24
SEP = chr(2)


def _flat(chunks):
    return SEP.join(chunks[i] for i in sorted(k for k in chunks if isinstance(k, int))).split(SEP)


def _one(c):
    return -1 if c == NIL else DEC[c]


def _multi(chars):
    if all(c == NIL for c in chars):
        return -1
    return sum(DEC[c] * (64 ** i) for i, c in enumerate(chars))


def decode(db):
    info = db["TSMItemInfoDB"]
    names = _flat(info["names"])
    strings = _flat(info["itemStrings"])
    data = info["data"]
    assert len(names) == len(strings) and len(data) == REC * len(names), (len(names), len(strings), len(data))
    items = {}
    for i, (s, n) in enumerate(zip(strings, names)):
        r = data[i * REC:(i + 1) * REC]
        items[s] = {
            "name": n,
            "itemLevel": _multi(r[0:2]),
            "minLevel": _multi(r[2:4]),
            "vendorSell": _multi(r[4:9]),
            "maxStack": _multi(r[9:11]),
            "invSlotId": _one(r[11]),
            "classId": _one(r[17]),
            "subClassId": _one(r[18]),
            "quality": _one(r[19]),
            "isBOP": _one(r[20]),
            "isCraftingReagent": _one(r[21]),
            "expansionId": _one(r[22]),
            "craftedQuality": _one(r[23]),
        }
    return items


def load_all(path):
    db = load(path)
    return db, decode(db)
