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

run("TC-SYM-009", "Max2 subroutine — BSUB/RET/CGT/BRF pattern (professor's pattern)",
    "TC-SYM-009.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("2 labels found", lambda c,o,f: "2 labels" in o.lower()),
        ("18 instructions encoded", lambda c,o,f: "18 instructions encoded" in o.lower()),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "18",
            "0100","0101","0300","0403","0301","0404","3210","0402","0202","9900",
            "0000","0303","2304","1216","0303","3300","0304","3300",
            "07",
            "9999","9999","0000","0000","0000"
        ])),
    ])

run("TC-SYM-010", "Multiple subroutines — AddTwo and Double called from main",
    "TC-SYM-010.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("2 labels found", lambda c,o,f: "2 labels" in o.lower()),
        ("22 instructions encoded", lambda c,o,f: "22 instructions encoded" in o.lower()),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "22",
            "0100","0101","0300","0403","0301","0404","3214","0402",
            "0302","0403","3218","0402","0202","9900",
            "0000","0303","0504","3300",
            "0000","0303","1503","3300",
            "08",
            "0000","0000","0000","0000","0000","0000"
        ])),
    ])

run("TC-SYM-011", "Array operations with subroutine — sum array elements via BSUB",
    "TC-SYM-011.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("1 labels found", lambda c,o,f: "1 labels" in o.lower()),
        ("20 instructions encoded", lambda c,o,f: "20 instructions encoded" in o.lower()),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "20",
            "3500","3600","0303","0405","3208","0403","0203","9900",
            "0000","0305","3900","0505","0405","4100","0304","1700","0404","1108","0305","3300",
            "08",
            "0010","0020","0030","0000","0003","0000"
        ])),
    ])

run("TC-SYM-013", "Find maximum in array — loop with CGT/BRF/iLOAD/iINCR",
    "TC-SYM-013.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("2 labels found", lambda c,o,f: "2 labels" in o.lower()),
        ("17 instructions encoded", lambda c,o,f: "17 instructions encoded" in o.lower()),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "17",
            "3500","3600","3900","0404","4100","3900","2304","1210",
            "3900","0404","4100","0306","1700","0406","1105","0204","9900",
            "07",
            "0005","0003","0008","0001","0000","0000","0004"
        ])),
    ])

run("TC-SYM-014", "Fibonacci loop — repeated ADD/STORE pattern with BRT",
    "TC-SYM-014.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("1 labels found", lambda c,o,f: "1 labels" in o.lower()),
        ("13 instructions encoded", lambda c,o,f: "13 instructions encoded" in o.lower()),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "13",
            "0300","0501","0402","0301","0400","0302","0401",
            "0303","1700","0403","1100","0201","9900",
            "05",
            "0001","0001","0000","0008","0000"
        ])),
    ])

run("TC-SYM-015", "Nested conditions with immediate arithmetic — ADDI/SUBI/MULTI/CGT/BRF",
    "TC-SYM-015.hal", [
        ("Exits with code 0", lambda c,o,f: c == 0),
        ("2 labels found", lambda c,o,f: "2 labels" in o.lower()),
        ("17 instructions encoded", lambda c,o,f: "17 instructions encoded" in o.lower()),
        ("Assembler execution OK", lambda c,o,f: "assembler execution ok" in o.lower()),
        (".hlx matches expected output", expect_hlx([
            "17",
            "0100","0101","0300","2510","0402","0301","2302","1212",
            "0301","2605","0403","1015","0300","2703","0403","0203","9900",
            "04",
            "0000","0000","0000","0000"
        ])),
    ])


if __name__ == "__main__":
    sys.exit(print_summary("TC-SYM"))