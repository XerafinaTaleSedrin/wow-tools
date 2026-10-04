"""Read-only summary of a TradeSkillMaster saved file: groups with item counts, and each
Auctioning operation's min price. Opens the file for reading only.

Usage:
    python tsm_groups.py                     # finds TradeSkillMaster.lua in the default WoW folders
    python tsm_groups.py path/to/TradeSkillMaster.lua
"""
import collections
import glob
import os
import sys

from svparse import load

SEP = chr(96)  # TSM separates group levels with a backtick
DEFAULT_GLOBS = [
    r"C:\Program Files (x86)\World of Warcraft\_retail_\WTF\Account\*\SavedVariables\TradeSkillMaster.lua",
    r"C:\Program Files\World of Warcraft\_retail_\WTF\Account\*\SavedVariables\TradeSkillMaster.lua",
    "/Applications/World of Warcraft/_retail_/WTF/Account/*/SavedVariables/TradeSkillMaster.lua",
]


def find_saved_file():
    hits = [p for g in DEFAULT_GLOBS for p in glob.glob(g)]
    if not hits:
        sys.exit("TradeSkillMaster.lua not found; pass its path as an argument")
    if len(hits) > 1:
        sys.exit("several accounts found; pass one path:\n  " + "\n  ".join(hits))
    return hits[0]


def summarize(db, profile="Default"):
    tsm = db["TradeSkillMasterDB"]
    items = tsm.get(f"p@{profile}@userData@items", {})
    ops = tsm.get(f"p@{profile}@userData@operations", {}).get("Auctioning", {})
    counts = collections.Counter(items.values())
    return counts, {name: op.get("minPrice") for name, op in ops.items()}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else find_saved_file()
    counts, min_prices = summarize(load(path))
    print("file:", os.path.basename(path))
    print("Auctioning operations (min price):")
    for name, price in sorted(min_prices.items()):
        print(f"  {name:30} {price}")
    print("Groups (items):")
    for name, n in sorted(counts.items()):
        print(f"  {name.replace(SEP, ' > '):50} {n}")
