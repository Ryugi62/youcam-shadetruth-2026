import json, os, re
from shadetruth.stats import readme_block

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_readme_numbers_match_recorded_runs():
    d = json.load(open(os.path.join(ROOT, "data", "drift.json")))
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    m = re.search(r"<!-- STATS -->\n(.*?)\n<!-- /STATS -->", readme, re.S)
    assert m, "README에 STATS 블록이 없다"
    assert m.group(1).strip() == readme_block(d).strip()


def test_docs_copy_of_data_is_identical():
    a = open(os.path.join(ROOT, "data", "drift.json"), "rb").read()
    b = open(os.path.join(ROOT, "docs", "data", "drift.json"), "rb").read()
    assert a == b
