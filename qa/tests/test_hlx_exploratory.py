#!/usr/bin/env python3
"""EXPLORATORY: Edge cases not covered by formal TCs."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_helpers import *

print("\n" + "="*60)
print(" EXPLORATORY: Edge Cases Found During Testing")
print("="*60)

print("\n------------------------------------------------------------")
print(" EXPLORATORY: Edge Cases Found During Testing")
print("------------------------------------------------------------")

run("EXPLORE-001", ".DATA with no value — assembles as 9999 uninitialized",
    "exploratory/explore_data_no_value.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx(["01","9900","01","9999"])),
    ])

run("EXPLORE-002", ".ALLOC 0 — valid, assembles with 0 data slots",
    "exploratory/explore_alloc_zero.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx(["01","9900","00"])),
    ])

run("EXPLORE-003", "BRANCH to itself — valid infinite loop encodes as 1000",
    "exploratory/explore_self_branch.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx(["02","1000","9900","01","0000"])),
    ])

run("EXPLORE-004", "Case insensitive variables — X and x treated as duplicate",
    "exploratory/explore_case_duplicate.hal", [
        ("Exits with non-zero code", expect_error),
        ("ERROR E007 duplicate variable", lambda c,o,f: "e007" in o.lower()),
        ("Variable X mentioned", lambda c,o,f: "'x'" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("EXPLORE-005", "Empty program — no instructions between .BEGIN and .END",
    "exploratory/explore_empty_program.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx(["00","01","0000"])),
    ])

run("EXPLORE-006", "ARR[5] out of bounds literal index — ERROR E030",
    "exploratory/explore_index_oob.hal", [
        ("Exits with non-zero code", expect_error),
        ("ERROR E030 reported", lambda c,o,f: "e030" in o.lower()),
        ("Exceeds block size mentioned", lambda c,o,f: "exceeds" in o.lower()),
        ("No .hlx produced", expect_no_hlx),
    ])

run("EXPLORE-007", "ARR[1] .DATA in data section — overwrites block element at assembly time",
    "exploratory/explore_block_data_set.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected — ARR[1] overwritten from 7 to 99", expect_hlx([
            "01","9900",
            "04",
            "0004","0099","0002","0000"
        ])),
    ])

if __name__ == "__main__":
    sys.exit(print_summary("EXPLORATORY"))