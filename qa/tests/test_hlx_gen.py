#!/usr/bin/env python3
"""TC-GEN: Code Generation & Output tests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_helpers import *

print("\n" + "="*60)
print(" TC-GEN: Code Generation & Output")
print("="*60)

run("TC-GEN-001", "Correct machine code generated for each instruction",
    "TC-GEN-001.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "06",
            "0100","0300","0701","0402","0202","9900",
            "03",
            "0003","0004","0000"
        ])),
    ])

run("TC-GEN-002", "Instructions before data in .hlx output",
    "TC-GEN-002.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx produced", expect_hlx_produced),
        (".hlx has instructions before data", expect_hlx([
            "03",
            "0300","0401","9900",
            "02",
            "0005","0000"
        ])),
    ])

run("TC-GEN-003", ".hlx output file produced with correct name",
    "TC-GEN-003.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hlx file produced", expect_hlx_produced),
        (".hlx matches expected output", expect_hlx([
            "02",
            "0200","9900",
            "01",
            "0007"
        ])),
    ])

run("TC-GEN-004", ".hll listing file produced",
    "TC-GEN-004.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        (".hll file produced", lambda c,o,f: os.path.isfile(f.replace(".hal",".hll"))),
        ("Output written message for .hll", lambda c,o,f: ".hll" in o.lower()),
    ])

run("TC-GEN-005", "Forward reference DONE resolves to correct address",
    "TC-GEN-005.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "08",
            "0300","2301","1106","1600","0400","1000","0200","9900",
            "02",
            "0001","0010"
        ])),
    ])

if __name__ == "__main__":
    sys.exit(print_summary("TC-GEN"))