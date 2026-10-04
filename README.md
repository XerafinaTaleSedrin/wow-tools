# wow-tools

Small Python tools for reading TradeSkillMaster (TSM) data outside World of Warcraft.

- **`tsm_import_decode.py`** decodes a TSM group import string (the text you paste into
  TSM's Import box) and shows the groups and items inside it, without importing anything.
  Useful for checking a public group string before it touches your setup, or for pulling
  out only the items.
- **`tsm_groups.py`** prints your groups with item counts, and the min price of each
  Auctioning operation, straight from TSM's saved file.
- **`svparse.py`** reads any WoW SavedVariables `.lua` file into Python dictionaries.
- **`itemdb.py`** decodes `TSMItemInfoDB`, TSM's cache of every item it has seen: name,
  item level, vendor sell price, item class and subclass, quality, expansion, and more.

Python 3.8+ and the standard library only. Nothing to install.

## Usage

```
python tsm_import_decode.py my-import-string.txt
python tsm_groups.py
python tsm_groups.py "C:\Program Files (x86)\World of Warcraft\_retail_\WTF\Account\<ACCOUNT>\SavedVariables\TradeSkillMaster.lua"
```

`tsm_import_decode.py` writes a `.decoded.json` next to the input file. `tsm_groups.py`
looks in the default Windows and macOS WoW folders when no path is given.

```python
from itemdb import load_all

db, items = load_all("path/to/TradeSkillMaster.lua")
herbs = {k: v for k, v in items.items() if v["classId"] == 7 and v["subClassId"] == 9}
```

## Editing TSM's file

These tools only read. If you write your own changes to `TradeSkillMaster.lua`:

- Close WoW completely first. The game rewrites the file on logout, reload and exit, and
  will overwrite your edit.
- Back up the file before every change.
- Parse the file again after editing, before starting the game.

## How the decoding works

An import string is TSM's printable encoding (LibDeflate `EncodeForPrint`) of raw
DEFLATE-compressed data serialized with LibSerialize. `tsm_import_decode.py` reverses
those three steps, following TSM's `GroupImport.lua`. `itemdb.py` follows TSM's
`ItemInfoSerializer.lua` record layout (24 characters per item).

Written against TSM 4.14 (retail, 2026). A future TSM update could change either format.

## Tests

```
python -m unittest discover tests
```

All test data is synthetic. `tests/encode_fixture.py` builds import strings so the
decoder can be tested without anyone's real export.

## Also here

`prompts/personal-wow-reference.md` is a prompt for having an AI assistant build a
personal reference page (profession specializations, class guides) from your own roster,
with sources cited.

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/): free to use, share and adapt with credit, not for commercial use. Not affiliated with TradeSkillMaster or Blizzard Entertainment.
