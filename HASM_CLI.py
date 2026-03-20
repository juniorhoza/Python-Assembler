#!/usr/bin/env python3

import argparse
import sys
import os

from services.HASM_opcode_Loader import load_opcode_table
from services.errors import ErrorHandler, color_error, color_warning
from services.lexer import tokenize_source, LexicalError
from services.pass1 import run_pass1, Pass1Error
from services.parser import parse_tokens, check_program_structure, ParserError
from services.pass2 import run_pass2, Pass2Error
from services.output import write_hlx, write_hll

BANNER = r"""

██╗  ██╗ █████╗ ██╗     ██╗██╗  ██╗        █████╗ ███████╗███████╗███████╗███╗   ███╗██████╗ ██╗     ███████╗██████╗
██║  ██║██╔══██╗██║     ██║╚██╗██╔╝       ██╔══██╗██╔════╝██╔════╝██╔════╝████╗ ████║██╔══██╗██║     ██╔════╝██╔══██╗
███████║███████║██║     ██║ ╚███╔╝        ███████║███████╗███████╗█████╗  ██╔████╔██║██████╔╝██║     █████╗  ██████╔╝
██╔══██║██╔══██║██║     ██║ ██╔██╗        ██╔══██║╚════██║╚════██║██╔══╝  ██║╚██╔╝██║██╔══██╗██║     ██╔══╝  ██╔══██╗
██║  ██║██║  ██║███████╗██║██╔╝ ██╗       ██║  ██║███████║███████║███████╗██║ ╚═╝ ██║██████╔╝███████╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═╝       ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝     ╚═╝╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝

Developed by Assembler Warriors

DEVs : frankjunior1.hozalon@famu.edu , javonte1.carter@famu.edu
QAs : ruxandra1.flueras@famu.edu , elizabeth1.uzoho@famu.edu

inspired by Dr. Jones's Halix Assembler
"""

USAGE_MSG = """
 -----------------------------------------------------------
 USAGE ERROR: ONE argument required.

 CORRECT USAGE:  python HASM_CLI.py source.hal

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


def _print_trace_pass1(pass1_result) -> None:
    print("\n[TRACE] PASS1 DATA TABLE")
    if not pass1_result.data_table:
        print("  <empty>")
    for entry in pass1_result.data_table.values():
        values = ", ".join(entry.values) if entry.values else entry.value
        print(
            f"  name={entry.name:<10} addr={entry.address} size={entry.size:<3} "
            f"values={values}"
        )

    print("\n[TRACE] PASS1 LABEL TABLE")
    if not pass1_result.label_table:
        print("  <empty>")
    for entry in pass1_result.label_table.values():
        print(f"  name={entry.name:<10} addr={entry.address} line={entry.line_number}")

    print("\n[TRACE] PASS1 LOCATION COUNTER")
    if not pass1_result.line_to_iaddr:
        print("  <empty>")
    for line_number, addr in pass1_result.line_to_iaddr.items():
        print(f"  line={line_number:>3} iaddr={addr}")

    print(
        f"\n[TRACE] PASS1 SUMMARY\n"
        f"  code_size={pass1_result.code_size:02d}\n"
        f"  data_size={pass1_result.data_size:02d}"
    )
    if pass1_result.warnings:
        print("  warnings:")
        for warning in pass1_result.warnings:
            print(f"    {warning}")


def _print_trace_pass2(pass2_result) -> None:
    print("\n[TRACE] PASS2 ENCODED INSTRUCTIONS")
    if not pass2_result.instructions:
        print("  <empty>")
    for instr in pass2_result.instructions:
        print(
            f"  line={instr.line_number:>3} iaddr={instr.iaddr} "
            f"word={instr.machine_word}  {instr.source_text}"
        )
    if pass2_result.errors:
        print("\n[TRACE] PASS2 ERRORS")
        for err in pass2_result.errors:
            print(f"  {err.code} line={err.line}: {err.message}")
    if pass2_result.warnings:
        print("\n[TRACE] PASS2 WARNINGS")
        for warning in pass2_result.warnings:
            print(f"  {warning.code} line={warning.line}: {warning.message}")


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
    try:
        with open(source_file) as f:
            source_lines = f.readlines()
    except OSError as e:
        error_handler.report(
            code="E000",
            message=f"Could not read source file '{source_file}': {e}",
            line=1,
            filename=source_file,
            is_fatal=True,
        )
        error_handler.emit_and_exit(3)

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
        error_handler.report(
            code=e.code,
            message=str(e),
            line=e.line,
            filename=source_file,
            is_fatal=True,
        )
        error_handler.emit_and_exit(6)

    print(f"Lexer OK: {len(lexer_tokens)} tokens generated.")
    if args.trace:
        _print_trace_tokens(lexer_tokens)

    # ------------------------------------------------------------------
    # Step 4: Parse token stream into statements
    # ------------------------------------------------------------------
    try:
        statements = parse_tokens(lexer_tokens, total_lines=len(source_lines))
    except ParserError as e:
        error_handler.report(
            code=e.code,
            message=str(e),
            line=e.line,
            filename=source_file,
            is_fatal=True,
        )
        error_handler.emit_and_exit(7)

    print(f"Parser OK: {len(statements)} statements generated.")
    if args.trace:
        _print_trace_statements(statements)

    # ------------------------------------------------------------------
    # Step 5: Validate program structure from parsed statements
    # ------------------------------------------------------------------
    structure_result = check_program_structure(statements)
    for warning in structure_result.warnings:
        print(color_warning(f"WARNING {warning.code}: {warning.message}"))

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

    # ------------------------------------------------------------------
    # Step 6: Pass 1 — build data/label tables and track location counters
    # ------------------------------------------------------------------
    try:
        pass1_result = run_pass1(statements)
    except Pass1Error as e:
        error_handler.report(
            code=e.code,
            message=str(e),
            line=e.line,
            filename=source_file,
            is_fatal=True,
        )
        error_handler.emit_and_exit(8)

    print(
        "Pass1 OK: "
        f"{len(pass1_result.data_table)} data symbols, "
        f"{len(pass1_result.label_table)} labels, "
        f"code_size={pass1_result.code_size:02d}, "
        f"data_size={pass1_result.data_size:02d}."
    )
    for warning in pass1_result.warnings:
        print(color_warning(f"WARNING: {warning}"))
    if args.trace:
        _print_trace_pass1(pass1_result)

    # ------------------------------------------------------------------
    # Step 7: Pass 2 — encode instructions to machine words
    # ------------------------------------------------------------------
    try:
        pass2_result = run_pass2(
            statements=statements,
            pass1_result=pass1_result,
            opcode_table=opcode_table,
            source_lines=source_lines,
        )
    except Pass2Error as e:
        error_handler.report(
            code=e.code,
            message=str(e),
            line=e.line,
            filename=source_file,
            is_fatal=True,
        )
        error_handler.emit_and_exit(9)

    for warning in pass2_result.warnings:
        warning_line = str(warning.line) if warning.line > 0 else "0"
        print(color_warning(f"{source_file}:{warning_line}: WARNING {warning.code}: {warning.message}"))

    if not pass2_result.ok:
        for err in pass2_result.errors:
            error_handler.report(
                code=err.code,
                message=err.message,
                line=err.line,
                filename=source_file,
                is_fatal=True,
            )
        error_handler.emit_and_exit(9)

    print(f"Pass2 OK: {len(pass2_result.instructions)} instructions encoded.")
    if args.trace:
        _print_trace_pass2(pass2_result)

    # ------------------------------------------------------------------
    # Step 8: Write output files (.hlx and .hll)
    # ------------------------------------------------------------------
    try:
        write_hlx(hlx_file, pass1_result, pass2_result)
        write_hll(
            hll_path=hll_file,
            source_file=source_file,
            hlx_path=hlx_file,
            pass1_result=pass1_result,
            pass2_result=pass2_result,
            source_lines=source_lines,
            statements=statements,
        )
    except OSError as e:
        error_handler.report(
            code="E000",
            message=f"Could not write output files: {e}",
            line=0,
            filename=source_file,
            is_fatal=True,
        )
        error_handler.emit_and_exit(10)

    print(f"Output written: {hlx_file}")
    print(f"Output written: {hll_file}")
    print("Assembler execution OK.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        print(color_error(f"Internal Assembler Error: {exc}"), file=sys.stderr)
        sys.exit(99)
