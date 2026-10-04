import re

BACKSLASH = chr(92)
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', BACKSLASH: BACKSLASH}
NUM_RE = re.compile(r"-?\d+(\.\d+)?([eE][-+]?\d+)?")
ID_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def tokenize(s):
    i, n = 0, len(s)
    toks = []
    while i < n:
        c = s[i]
        if c in " \t\r\n":
            i += 1
            continue
        if s.startswith("--", i):
            j = s.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == '"':
            j = i + 1
            buf = []
            while True:
                d = s[j]
                if d == BACKSLASH:
                    e = s[j + 1]
                    buf.append(ESCAPES.get(e, e))
                    j += 2
                elif d == '"':
                    break
                else:
                    buf.append(d)
                    j += 1
            toks.append(("str", "".join(buf)))
            i = j + 1
            continue
        if c.isdigit() or (c == "-" and i + 1 < n and s[i + 1].isdigit()):
            m = NUM_RE.match(s, i)
            v = m.group(0)
            toks.append(("num", float(v) if ("." in v or "e" in v.lower()) else int(v)))
            i = m.end()
            continue
        m = ID_RE.match(s, i)
        if m:
            toks.append(("id", m.group(0)))
            i = m.end()
            continue
        toks.append(("sym", c))
        i += 1
    return toks


def parse(toks):
    pos = 0

    def val():
        nonlocal pos
        t, v = toks[pos]
        if t == "sym" and v == "{":
            pos += 1
            d = {}
            idx = 1
            while toks[pos] != ("sym", "}"):
                if toks[pos] == ("sym", "["):
                    pos += 1
                    k = val()
                    assert toks[pos] == ("sym", "]"), toks[pos]
                    pos += 1
                    assert toks[pos] == ("sym", "="), toks[pos]
                    pos += 1
                    d[k] = val()
                elif toks[pos][0] == "id" and toks[pos + 1] == ("sym", "="):
                    k = toks[pos][1]
                    pos += 2
                    d[k] = val()
                else:
                    d[idx] = val()
                    idx += 1
                if toks[pos] in (("sym", ","), ("sym", ";")):
                    pos += 1
            pos += 1
            return d
        pos += 1
        if t == "id":
            return {"true": True, "false": False, "nil": None}.get(v, v)
        return v

    out = {}
    while pos < len(toks):
        name = toks[pos][1]
        assert toks[pos + 1] == ("sym", "="), toks[pos + 1]
        pos += 2
        out[name] = val()
    return out


def load(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return parse(tokenize(fh.read()))
