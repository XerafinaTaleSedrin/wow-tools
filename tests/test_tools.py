"""All fixtures are synthetic. Run from the repo root: python -m unittest discover tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import itemdb  # noqa: E402
import svparse  # noqa: E402
import tsm_groups  # noqa: E402
import tsm_import_decode as dec  # noqa: E402
from encode_fixture import build_import, encode_for_print  # noqa: E402

SAVED = r'''
TradeSkillMasterDB = {
	["p@Default@userData@items"] = {
		["i:2589"] = "Mats`Cloth",
		["i:2592"] = "Mats`Cloth",
		["i:858"] = "Consumables",
	},
	["p@Default@userData@operations"] = {
		["Auctioning"] = {
			["Mats"] = { ["minPrice"] = "max(1.06 * vendorsell, 0.8 * DBMarket)", },
		},
	},
	["s@Example - Realm@internalData@money"] = -12.5e2,
	["flag"] = true, -- a comment
	["list"] = { "a", "b\"c", 3, },
}
'''


class SvParse(unittest.TestCase):
    def test_parses_nested_tables_numbers_escapes(self):
        db = svparse.parse(svparse.tokenize(SAVED))["TradeSkillMasterDB"]
        self.assertEqual(db["p@Default@userData@items"]["i:858"], "Consumables")
        self.assertEqual(db["s@Example - Realm@internalData@money"], -1250.0)
        self.assertIs(db["flag"], True)
        self.assertEqual(db["list"], {1: "a", 2: 'b"c', 3: 3})

    def test_groups_summary(self):
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8") as fh:
            fh.write(SAVED)
        try:
            counts, prices = tsm_groups.summarize(svparse.load(fh.name))
        finally:
            os.unlink(fh.name)
        self.assertEqual(counts["Mats`Cloth"], 2)
        self.assertEqual(counts["Consumables"], 1)
        self.assertIn("vendorsell", prices["Mats"])


class ItemDb(unittest.TestCase):
    def test_decodes_one_record(self):
        a = itemdb.ALPHABET
        nil = itemdb.NIL
        # itemLevel 70 -> "G" "B" (6 + 1*64), minLevel nil, vendorSell 5, maxStack 200, then single fields
        rec = (a[6] + a[1] + nil + nil + a[5] + a[0] * 4 + a[8] + a[3] + nil
               + nil * 5 + a[7] + a[5] + a[1] + a[0] + a[1] + a[11] + nil)
        self.assertEqual(len(rec), itemdb.REC)
        db = {"TSMItemInfoDB": {"names": {1: "Test Cloth"}, "itemStrings": {1: "i:1"}, "data": rec}}
        item = itemdb.decode(db)["i:1"]
        self.assertEqual(item["name"], "Test Cloth")
        self.assertEqual(item["itemLevel"], 70)
        self.assertEqual(item["minLevel"], -1)
        self.assertEqual(item["vendorSell"], 5)
        self.assertEqual(item["maxStack"], 200)
        self.assertEqual(item["classId"], 7)
        self.assertEqual(item["expansionId"], 11)
        self.assertEqual(item["craftedQuality"], -1)


class ImportDecode(unittest.TestCase):
    def test_print_codec_round_trip(self):
        for raw in (b"", b"a", b"ab", b"abc", bytes(range(256))):
            self.assertEqual(dec.decode_for_print(encode_for_print(raw)), raw)

    def test_decodes_synthetic_group_export(self):
        items = {f"i:{1000 + n}": ("Example`Herbs" if n % 2 else "Example`Ore") for n in range(20)}
        s = build_import(["TSM_EXPORT", 2, "Example", items,
                          {"Example": True, "Example`Herbs": True, "Example`Ore": True}, {}, {}, {}])
        self.assertFalse(set(s) - set(dec.SIX))
        imp = dec.decode_import(s)
        self.assertEqual(imp["groupName"], "Example")
        self.assertEqual(imp["items"], items)
        self.assertEqual(set(imp["groups"]), {"Example", "Example`Herbs", "Example`Ore"})


if __name__ == "__main__":
    unittest.main()
