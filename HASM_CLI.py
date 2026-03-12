#!/usr/bin/env python3

import argparse
import sys
import os

from services.HASM_opcode_Loader import load_opcode_table
from services.errors import ErrorHandler, color_error
from services.lexer import tokenize_source, LexicalError
from services.parser import parse_tokens, check_program_structure, ParserError

BANNER = r"""

 _   _    _    _     _____  __   _     ___  ____  _____ ______ _____ __    _____ ____
| | | |  / \  | |   |_ _\ \/ /  / \  / ___|| ___|| ____|  \/  | __ )| |   | ____|  _ \
| |_| | / _ \ | |    | | \  /  / _ \ \___ \|___ \|  _| | |\/| |  _ \| |   |  _| | |_) |
|  _  |/ ___ \| |___ | | /  \ / ___ \ ___) |___) | |___| |  | | |_) | |___| |___|  _ <
|_| |_/_/   \_\_____|___/_/\_/_/   \_\____/|____/|_____|_|  |_|____/|_____|_____|_| \_\



developed by Assembler Warriors

devs : frankjunior1.hozalon@famu.edu , javonte1.carter@famu.edu
QA : ruxandra1.flueras@famu.edu , elizabeth1.uzoho@famu.edu

inspired by Dr jones's Halix assembler
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
DEFAULT_OPCODE_PATH = os.path.join(_HERE, "halix_v25.opcode")


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
        help="Path to opcode table file (default: ./halix_v25.opcode)",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print lexer tokens and parser statements for debugging.",
    )
    return parser


def validate_args(source_file: str, error_handler: ErrorHandler) -> str:
    if not source_file.endswith(".hal"):
        error_handler.report(
            code="E001",
            message=f"Input file '{source_file}' must have .hal extension.",
            line=1,
            filename=source_file,
            is_fatal=True,
        )
        error_handler.emit_and_exit(2)
    if not os.path.isfile(source_file):
        error_handler.report(
            code="E000",
            message=f"Input file '{source_file}' NOT FOUND - FATAL.",
            line=1,
            filename=source_file,
            is_fatal=True,
        )
        error_handler.emit_and_exit(3)
    return source_file


def derive_output_paths(source_file: str) -> tuple[str, str]:
    base = source_file[:-4]
    return base + ".hlx", base + ".hll"


def _print_trace_tokens(tokens) -> None:
    print("\n[TRACE] LEXER TOKENS")
    for tok in tokens:
        print(
            f"  line={tok.line_number:>3} col={tok.column:>3} "
            f"type={tok.token_type:<10} value={tok.value}"
        )


def _print_trace_statements(statements) -> None:
    print("\n[TRACE] PARSER STATEMENTS")
    for st in statements:
        label = st.label if st.label is not None else "-"
        mnemonic = st.mnemonic if st.mnemonic is not None else "-"
        operands = ", ".join(st.operands) if st.operands else "-"
        print(
            f"  line={st.line_number:>3} kind={st.kind:<11} "
            f"label={label:<10} mnemonic={mnemonic:<8} operands={operands}"
        )


def main():
    print_banner()

    if len(sys.argv) == 1:
        print(USAGE_MSG)
        sys.exit(1)

    parser = build_parser()
    args = parser.parse_args()

    error_handler = ErrorHandler(default_filename=args.source_file)

    source_file = validate_args(args.source_file, error_handler)
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
        opcode_table = load_opcode_table(args.opcode_table)
    except (FileNotFoundError, ValueError) as e:
        error_handler.report(
            code="E000",
            message=str(e),
            line=0,
            filename=source_file,
            is_fatal=True,
        )
        error_handler.emit_and_exit(4)

    # ------------------------------------------------------------------
    # Step 2: Read source file
    # ------------------------------------------------------------------
    with open(source_file) as f:
        source_lines = f.readlines()

    # ------------------------------------------------------------------
    # Step 3: Lex source to tokens (labels, mnemonics, operands, comments)
    # ------------------------------------------------------------------
    try:
        lexer_tokens = tokenize_source(
            source_lines=source_lines,
            opcode_mnemonics=set(opcode_table.by_mnemonic.keys()),
            keep_comments=True,
        )
    except LexicalError as e:
        print(color_error(str(e)), file=sys.stderr)
        sys.exit(6)

    print(f"Lexer OK: {len(lexer_tokens)} tokens generated.")
    if args.trace:
        _print_trace_tokens(lexer_tokens)

    # ------------------------------------------------------------------
    # Step 4: Parse token stream into statements
    # ------------------------------------------------------------------
    try:
        statements = parse_tokens(lexer_tokens, total_lines=len(source_lines))
    except ParserError as e:
        print(color_error(str(e)), file=sys.stderr)
        sys.exit(7)

    print(f"Parser OK: {len(statements)} statements generated.")
    if args.trace:
        _print_trace_statements(statements)

    # ------------------------------------------------------------------
    # Step 5: Validate program structure from parsed statements
    # ------------------------------------------------------------------
    structure_result = check_program_structure(statements)
    for warning in structure_result.warnings:
        print(f"WARNING {warning.code}: {warning.message}")

    if not structure_result.ok:
        for issue in structure_result.errors:
            error_handler.report(
                code=issue.code,
                message=issue.message,
                line=issue.line,
                filename=source_file,
                is_fatal=issue.is_fatal,
            )
        error_handler.emit_and_exit(5)

    print(f"Program structure OK [{source_file}].")

    print("[CLI OK] Opcode table loaded, lexer/parser completed, structure validation passed.")


if __name__ == "__main__":
    main()
