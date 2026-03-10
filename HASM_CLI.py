#!/usr/bin/env python3
"""
hasm_cli.py
-----------
CLI entry point for the Halix Assembler (Python implementation).

Confirmed legacy behavior replicated:
  - Exactly one positional argument required.
  - Source file must have .hal extension.
  - Version banner printed on every run.
  - Exit codes:
      1 -> wrong number of arguments
      2 -> wrong file extension
      3 -> file not found
      4 -> opcode table missing or invalid
      5 -> directive structure invalid

Client requirements addressed here:
  - Opcode table loaded dynamically (no hard-coded opcodes).
  - Directive structure validated before assembly begins.
  - Rich error reporting to console and listing file.
"""

import argparse
import sys
import os

from hasm_directive_checker import check_directives, report_results
from hasm_opcode_loader import load_opcode_table

BANNER = """
Halix Assembler version 11 / 2012 Jan 23 (c) EL Jones
Halix Assembler version 13 / 2024 Nov 20 (c) EL Jones
Halix Assembler version v25 / 2025 Mar 22 (c) EL Jones
[Python port — team implementation]
"""

USAGE_MSG = """
 -----------------------------------------------------------
 USAGE ERROR: ONE argument required.

 CORRECT USAGE:  python hasm_cli.py source.hal

    where:

        source.hal -- file containing assembly language code.

 -----------------------------------------------------------
"""

# Path to the opcode table — relative to this script's location
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OPCODE_PATH = os.path.join(
    _HERE, "..", "Halix_Software", "halix_v25.opcode"
)
DEFAULT_CFG_PATH = os.path.join(
    _HERE, "..", "Halix_Software", "halix_v25.opcode.cfg"
)


def print_banner():
    print(BANNER)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hasm",
        description="Halix Assembler — translates .hal source to .hlx machine code and .hll listing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Output files are derived from the source filename:\n"
            "  source.hal  ->  source.hlx  (machine code)\n"
            "                  source.hll  (assembler listing)\n"
        ),
        add_help=True,
    )
    parser.add_argument(
        "source_file",
        help="Halix assembly source file (must have .hal extension)",
    )
    parser.add_argument(
        "--opcode-table",
        default=DEFAULT_OPCODE_PATH,
        help="Path to opcode table file (default: Halix_Software/halix_v25.opcode)",
    )
    parser.add_argument(
        "--opcode-cfg",
        default=DEFAULT_CFG_PATH,
        help="Path to opcode operand-type config (default: Halix_Software/halix_v25.opcode.cfg)",
    )
    return parser


def validate_args(source_file: str) -> str:
    if not source_file.endswith(".hal"):
        print(f"Input file '{source_file}' must have .hal extension.")
        sys.exit(2)
    if not os.path.isfile(source_file):
        print(f"Input file '{source_file}' NOT FOUND - FATAL.")
        sys.exit(3)
    return source_file


def derive_output_paths(source_file: str) -> tuple[str, str]:
    base = source_file[:-4]
    return base + ".hlx", base + ".hll"


def main():
    print_banner()

    if len(sys.argv) == 1:
        print(USAGE_MSG)
        sys.exit(1)

    parser = build_parser()
    args = parser.parse_args()

    source_file = validate_args(args.source_file)
    hlx_file, hll_file = derive_output_paths(source_file)

    print("****  HASM EXECUTION STARTING ...")
    print(f"  Source:  {source_file}")
    print(f"  Output:  {hlx_file}  (machine code)")
    print(f"           {hll_file}  (listing)")
    print()

    # ------------------------------------------------------------------
    # Step 1: Load opcode table dynamically — NO hard-coded opcodes
    # ------------------------------------------------------------------
    try:
        opcode_table = load_opcode_table(args.opcode_table, args.opcode_cfg)
    except (FileNotFoundError, ValueError) as e:
        print(str(e))
        sys.exit(4)

    # ------------------------------------------------------------------
    # Step 2: Validate directive structure
    # ------------------------------------------------------------------
    with open(source_file) as f:
        source_lines = f.readlines()

    directive_result = check_directives(source_lines)
    report_results(directive_result, source_file)

    if not directive_result.ok:
        sys.exit(5)

    # ------------------------------------------------------------------
    # Step 3: Hand off to assembler pipeline (future modules)
    # ------------------------------------------------------------------
    # from hasm_pass1 import run_pass1
    # from hasm_pass2 import run_pass2
    # from hasm_output import write_output
    #
    # symbol_tables = run_pass1(source_lines, directive_result, opcode_table)
    # object_code   = run_pass2(source_lines, directive_result, symbol_tables, opcode_table)
    # write_output(object_code, hlx_file, hll_file)

    print("[CLI OK] Opcode table loaded and directive validation passed. Pipeline not yet connected.")


if __name__ == "__main__":
    main()
```

---

## Updated file layout
```
project-test-bed/
├── Halix_Software/
│   ├── halix_v25.opcode        ← existing, unchanged
│   ├── halix_v25.opcode.cfg    ← NEW — operand type config
│   └── ...
└── Python-Assembler/
    ├── hasm_cli.py              ← updated
    ├── hasm_directive_checker.py ← updated (.BLOCK added)
    ├── hasm_opcode_loader.py    ← NEW
    └── (future: pass1, pass2, output, error handler)