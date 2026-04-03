#!/usr/bin/env python3
"""TC-SYM: Symbol Management tests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_helpers import *

print("\n" + "="*60)
print(" TC-SYM: Symbol Management")
print("="*60)

run("TC-SYM-001", "Symbol table — 4 labels with correct addresses",
    "TC-SYM-001.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("4 labels found in Pass1", lambda c,o,f: "4 labels" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "11",
            "0300","0501","0402","2302","1109",
            "0300","1600","0400","1005","0202","9900",
            "03",
            "0001","0002","0000"
        ])),
    ])

run("TC-SYM-002", "Duplicate label LOOP — error E007 with line number, no .hlx produced",
    "TC-SYM-002.hal", [
        ("Error E007 reported", lambda c,o,f: "e007" in o.lower()),
        ("Duplicate label LOOP mentioned", lambda c,o,f: "duplicate" in o.lower() and "loop" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-SYM-003", "Undefined label MISSING — error E021, no .hlx produced",
    "TC-SYM-003.hal", [
        ("Error E021 reported", lambda c,o,f: "e021" in o.lower() or "undefined" in o.lower()),
        ("MISSING label mentioned", lambda c,o,f: "missing" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("TC-SYM-005", "Opcode table — 14 instructions all encoded correctly",
    "TC-SYM-005.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("14 instructions encoded", lambda c,o,f: "14 instructions encoded" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "14",
            "0100","0300","0501","0601","0701","0801",
            "0402","0202","1600","1700","1300","1113","1013","9900",
            "05",
            "0001","0002","0000","0005"
        ])),
    ])

run("TC-SYM-006", "Location counter — 5 instructions at sequential addresses",
    "TC-SYM-006.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("5 instructions encoded", lambda c,o,f: "5 instructions encoded" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "05",
            "0300","0401","0201","1000","9900",
            "02",
            "0005","0000"
        ])),
    ])


if __name__ == "__main__":
    sys.exit(print_summary("TC-SYM"))