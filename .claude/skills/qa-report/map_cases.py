#!/usr/bin/env python3
"""Join pytest results to ticket test cases and print JSON rows.

usage: map_cases.py JUNIT_XML T-019=tests/test_login.py,tests/test_auth.py T-020=tests/test_users.py ...

A test belongs to case TC-n when its `def` line (or a line inside it) carries `# TC-n` (or `# T-NNN TC-n`) and
its file is listed for that ticket. Cases come from the `| TC-n |` rows of plans/tickets/<ticket>.md.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

junit, *pairs = sys.argv[1:]
ticket_files = {t: f.split(",") for t, f in (p.split("=", 1) for p in pairs)}

status = {}  # "tests/test_x.py::name" -> pass | fail | skip
for tc in ET.parse(junit).getroot().iter("testcase"):
    name = (tc.get("name") or "").split("[")[0]  # parametrised runs: any failure fails the test
    key = (tc.get("classname") or "").replace(".", "/") + ".py::" + name
    s = "fail" if tc.find("failure") is not None or tc.find("error") is not None else "skip" if tc.find("skipped") is not None else "pass"
    if status.get(key) != "fail":
        status[key] = s

tests = {}  # (ticket, "TC-n") -> [test ids]
claimed = set()
for ticket, files in ticket_files.items():
    for f in files:
        func = None
        for line in Path(f).read_text().splitlines():
            m = re.match(r"\s*def (test_\w+)", line)
            if m:
                func = m.group(1)
            for t, n in re.findall(r"#.*?(?:(T-\d+)\s+)?(TC-\d+)", line):
                if func and t in ("", ticket):
                    tests.setdefault((ticket, n), []).append(f"{f}::{func}")
                    claimed.add(f"{f}::{func}")

rows = []
for ticket in ticket_files:
    for n, when in re.findall(r"^\|\s*(TC-\d+)\s*\|[^|]*\|[^|]*\|[^|]*\|\s*([^|]*?)\s*\|", Path(f"plans/tickets/{ticket}.md").read_text(), re.M):
        ids = tests.get((ticket, n), [])
        results = [status.get(i, "missing") for i in ids]
        result = "no test" if not ids else "fail" if "fail" in results else "pass" if all(r == "pass" for r in results) else "skip"
        rows.append({"ticket": ticket, "case": n, "when": when, "tests": ids, "result": result})

print(json.dumps({"cases": rows, "tests_without_case": sorted(k for k in status if k.split("::")[0] in {f for fs in ticket_files.values() for f in fs} and k not in claimed)}, indent=1))
