#!/usr/bin/env python3

import argparse
import sys
import os

from services.HASM_opcode_Loader import load_opcode_table
from services.errors import ErrorHandler, color_error, color_warning
from services.lexer import tokenize_source_collect
from services.pass1 import run_pass1
from services.parser import parse_tokens_collect, check_program_structure
from services.pass2 import run_pass2, Pass2Error
from services.output import write_hlx, write_hll, write_sym

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
            "\n"
            "Custom output basename:\n"
            "  hasm source.hal -o build/out  ->  build/out.hlx, build/out.hll\n"
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
    parser.add_argument(
        "--cols",
        help="Column widths for .hll source formatting as LABEL,MNEMONIC (example: --cols 8,10).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Custom output basename. Generates <output>.hlx and <output>.hll.",
    )
    parser.add_argument(
        "-s",
        action="store_true",
        help="Write DataTable and LabelTable dump to a .sym file.",
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


def derive_output_paths(source_file: str, output_base: str | None = None) -> tuple[str, str, str]:
    base = output_base if output_base is not None else source_file[:-4]
    if base.endswith(".hlx") or base.endswith(".hll"):
        base = os.path.splitext(base)[0]
    return base + ".hlx", base + ".hll", base + ".sym"


def _parse_cols_value(raw_value: str) -> tuple[int, int]:
    parts = [part.strip() for part in raw_value.split(",")]
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError("expected format LABEL,MNEMONIC with numeric values")
    return int(parts[0]), int(parts[1])


def _resolve_hconfig_path(source_file: str) -> str | None:
    source_dir = os.path.dirname(os.path.abspath(source_file))
    source_config = os.path.join(source_dir, ".hconfig")
    if os.path.isfile(source_config):
        return source_config

    cwd_config = os.path.join(os.getcwd(), ".hconfig")
    if os.path.isfile(cwd_config):
        return cwd_config
    return None


def resolve_listing_columns(args, error_handler: ErrorHandler, source_file: str) -> tuple[int, int] | None:
    default_label_width = 8
    default_mnemonic_width = 8

    raw_value: str | None = None
    config_path = None

    if args.cols is not None:
        raw_value = args.cols
    else:
        config_path = _resolve_hconfig_path(source_file)
        if config_path is not None:
            try:
                with open(config_path, "r", encoding="utf-8") as config_file:
                    raw_value = config_file.readline().strip()
            except OSError as e:
                error_handler.report(
                    code="E000",
                    message=f"Could not read configuration file '{config_path}': {e}",
                    line=0,
                    filename=source_file,
                    is_fatal=True,
                )
                error_handler.emit_and_exit(2)

    if raw_value is None or raw_value == "":
        return None

    if raw_value.startswith("[") and raw_value.endswith("]"):
        raw_value = raw_value[1:-1].strip()

    try:
        label_width, mnemonic_width = _parse_cols_value(raw_value)
    except ValueError as e:
        source_hint = "--cols" if args.cols is not None else config_path or ".hconfig"
        error_handler.report(
            code="E009",
            message=f"Invalid column configuration in {source_hint}: {e}.",
            line=0,
            filename=source_file,
            is_fatal=True,
        )
        error_handler.emit_and_exit(2)

    for field_name, width in (("label", label_width), ("mnemonic", mnemonic_width)):
        if width > 10:
            error_handler.report(
                code="E009",
                message=f"{field_name} column width {width} exceeds maximum allowed value 10.",
                line=0,
                filename=source_file,
                is_fatal=True,
            )
            error_handler.emit_and_exit(2)

    if label_width < default_label_width:
        print(
            color_warning(
                f"{source_file}:0: WARNING W006: label column width {label_width} is below default "
                f"{default_label_width}; using {default_label_width}."
            )
        )
        label_width = default_label_width

    if mnemonic_width < default_mnemonic_width:
        print(
            color_warning(
                f"{source_file}:0: WARNING W007: mnemonic column width {mnemonic_width} is below default "
                f"{default_mnemonic_width}; using {default_mnemonic_width}."
            )
        )
        mnemonic_width = default_mnemonic_width

    return label_width, mnemonic_width


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
    source_columns = resolve_listing_columns(args, error_handler, source_file)
    hlx_file, hll_file, sym_file = derive_output_paths(source_file, args.output)

    print("****  HASM EXECUTION STARTING ...")
    print(f"  Source:  {source_file}")
    print(f"  Output:  {hlx_file}  (machine code)")
    print(f"           {hll_file}  (listing)")
    if args.s:
        print(f"           {sym_file}  (symbol dump)")
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
    lexer_tokens, lexical_errors = tokenize_source_collect(
        source_lines=source_lines,
        opcode_mnemonics=set(opcode_table.by_mnemonic.keys()),
        keep_comments=True,
    )
    for err in lexical_errors:
        error_handler.report(
            code=err.code,
            message=str(err),
            line=err.line,
            filename=source_file,
            is_fatal=True,
        )
    if lexical_errors:
        error_handler.emit_and_exit(6)

    print(f"Lexer OK: {len(lexer_tokens)} tokens generated.")
    if args.trace:
        _print_trace_tokens(lexer_tokens)

    # ------------------------------------------------------------------
    # Step 4: Parse token stream into statements
    # ------------------------------------------------------------------
    statements, parser_errors = parse_tokens_collect(lexer_tokens, total_lines=len(source_lines))
    for err in parser_errors:
        error_handler.report(
            code=err.code,
            message=str(err),
            line=err.line,
            filename=source_file,
            is_fatal=True,
        )

    print(f"Parser OK: {len(statements)} statements generated.")
    if args.trace:
        _print_trace_statements(statements)

    # ------------------------------------------------------------------
    # Step 5: Validate program structure from parsed statements
    # ------------------------------------------------------------------
    structure_result = check_program_structure(statements)
    for warning in structure_result.warnings:
        print(color_warning(f"WARNING {warning.code}: {warning.message}"))

    if parser_errors or not structure_result.ok:
        for issue in structure_result.errors:
            error_handler.report(
                code=issue.code,
                message=issue.message,
                line=issue.line,
                filename=source_file,
                is_fatal=issue.is_fatal,
            )
        exit_code = 7 if parser_errors else 5
        error_handler.emit_and_exit(exit_code)

    print(f"Program structure OK [{source_file}].")

    # ------------------------------------------------------------------
    # Step 6: Pass 1 — build data/label tables and track location counters
    # ------------------------------------------------------------------
    pass1_result = run_pass1(statements)
    if pass1_result.errors:
        for err in pass1_result.errors:
            error_handler.report(
                code=err.code,
                message=str(err),
                line=err.line,
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
            source_columns=source_columns,
        )
        if args.s:
            write_sym(sym_file, pass1_result)
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
    if args.s:
        print(f"Output written: {sym_file}")
    print("Assembler execution OK.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        print(color_error(f"Internal Assembler Error: {exc}"), file=sys.stderr)
        sys.exit(99)
