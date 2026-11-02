import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shadetruth.stats import readme_block
d = json.load(open("data/drift.json"))
t = open("README.md", encoding="utf-8").read()
t = re.sub(r"<!-- STATS -->\n.*?\n?<!-- /STATS -->", lambda m: "<!-- STATS -->\n" + readme_block(d) + "\n<!-- /STATS -->", t, flags=re.S)
open("README.md", "w", encoding="utf-8").write(t)
