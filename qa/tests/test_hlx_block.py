#!/usr/bin/env python3
"""TC-BLOCK: New .BLOCK Array Feature tests (SCRUM-59)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_helpers import *

print("\n" + "="*60)
print(" TC-BLOCK: New .BLOCK Array Feature (SCRUM-59)")
print("="*60)

print("\n------------------------------------------------------------")
print(" TC-BLOCK: .BLOCK New Syntax & Indexed Access (SCRUM-59)")
print("------------------------------------------------------------")

run("TC-BLOCK-001", ".BLOCK initialized =4,=7,=2 — indexed access ARR[0]",
    "TC-BLOCK-001.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "05",
            "3500","3600","3900","0403","9900",
            "04",
            "0004","0007","0002","0000"
        ])),
    ])

run("TC-BLOCK-002", ".BLOCK empty format — 5 uninitialized slots",
    "TC-BLOCK-002.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "01",
            "9900",
            "06",
            "9999","9999","9999","9999","9999","0000"
        ])),
    ])

run("TC-BLOCK-003", ".BLOCK indexed access ARR[0], ARR[1], ARR[2]",
    "TC-BLOCK-003.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "11",
            "3500","3600","3900","0403","4100","3900","0403","4100","3900","0403","9900",
            "04",
            "0010","0020","0030","0000"
        ])),
    ])

run("TC-BLOCK-004", ".BLOCK single value =99 — assembles correctly",
    "TC-BLOCK-004.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "01",
            "9900",
            "03",
            "0099","0000"
        ])),
    ])

run("TC-BLOCK-005", "Single-value .BLOCK indexed access ARR[0] — BUG-002",
    "TC-BLOCK-005.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "04",
            "3500","3600","3900","9900",
            "01",
            "0099"
        ])),
    ])

run("TC-BLOCK-006", ".BLOCK variable index LOAD ARR[i] — dynamic array access",
    "TC-BLOCK-006.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "06",
            "3500","3600","4100","3900","0403","9900",
            "05",
            "0004","0007","0002","0000"
        ])),
    ])

run("TC-BLOCK-007", "STORE ARR[i] — indexed element set via variable index (PENDING-001 resolved)",
    "TC-BLOCK-007.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "06",
            "3500","3600","4100","0303","4000","9900",
            "04",
            "0004","0007","0002","0099"
        ])),
    ])

run("TC-BLOCK-008", ".BLOCK dynamic array loop — iLOAD/iINCR pattern",
    "TC-BLOCK-008.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "08",
            "3500","3600","3900","0403","4100","0303","1102","9900",
            "05",
            "0004","0007","0002","0000"
        ])),
    ])

run("TC-BLOCK-009", ".BLOCK lowercase mnemonics — case insensitive (loada/iclr/iload)",
    "TC-BLOCK-009.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "05",
            "3500","3600","3900","0403","9900",
            "04",
            "0004","0007","0002","0000"
        ])),
    ])

if __name__ == "__main__":
    sys.exit(print_summary("TC-BLOCK"))