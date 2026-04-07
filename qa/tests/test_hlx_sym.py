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

run("TC-SYM-007", "New i-instructions all encoded correctly — iREAD/iWRITE/iDECR/iADD etc",
    "TC-SYM-007.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("17 instructions encoded", lambda c,o,f: "17 instructions encoded" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "17",
            "3500","3600","3700","3800","4200","4300","4400","4500","4600","4700",
            "4800","4900","5000","5100","5200","5300","9900",
            "04",
            "0001","0002","0003","0000"
        ])),
    ])

run("TC-SYM-008", "New scalar/control instructions — SETI/ADDI/POW/SHACC/STOREA/BSUB/RET etc",
    "TC-SYM-008.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("32 instructions encoded", lambda c,o,f: "32 instructions encoded" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "32",
            "3500","3600","2405","2503","2602","2704","2802","2903",
            "3100","3400","5400","5500","5600","5700","5805","5904",
            "3003","0000","0303","1503","0904","1400","1804","1904",
            "2004","2104","2204","2304","1230","3230","3300","9900",
            "06",
            "0001","0002","0003","0005","0003","0000"
        ])),
    ])

if __name__ == "__main__":
    sys.exit(print_summary("TC-SYM"))