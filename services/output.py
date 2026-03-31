"""
services/output.py
------------------
Writes the .hlx machine code file and .hll listing file.

SCRUM-23: FR-GEN-002, FR-GEN-003, FR-GEN-004
"""

from services.pass1 import Pass1Result
from services.pass2 import Pass2Result


# -----------------------------------------------------------------------
# .hlx writer
# -----------------------------------------------------------------------

def write_hlx(hlx_path: str, pass1_result: Pass1Result, pass2_result: Pass2Result) -> None:
    """
    Write the Halix machine code file (.hlx).
    Format must match HASM_v25.csh output exactly.
    """
    with open(hlx_path, "w") as f:

        # Line 1: code size (2-digit zero-padded)
        f.write(f"{pass1_result.code_size:02d}\n")

        # One machine word per instruction in address order
        for instr in sorted(pass2_result.instructions, key=lambda x: int(x.iaddr)):
            f.write(f"{instr.machine_word}\n")

        # Data memory size
        f.write(f"{pass1_result.data_size:02d}\n")

        # Data values in address order
        sorted_data = sorted(
            pass1_result.data_table.values(),
            key=lambda e: int(e.address)
        )
        for entry in sorted_data:
            # .BLOCK entries write all their values sequentially
            for val in entry.values:
                f.write(f"{val}\n")


# -----------------------------------------------------------------------
# .sym writer
# -----------------------------------------------------------------------

def write_sym(sym_path: str, pass1_result: Pass1Result) -> None:
    """Write the symbol table dump (.sym)."""
    with open(sym_path, "w") as f:
        f.write("DataTable\n")
        f.write("---------\n")
        if not pass1_result.data_table:
            f.write("<empty>\n")
        else:
            for entry in sorted(pass1_result.data_table.values(), key=lambda e: int(e.address)):
                values = ", ".join(entry.values)
                f.write(
                    f"{entry.name} addr={entry.address} size={entry.size} values=[{values}]\n"
                )

        f.write("\n")
        f.write("LabelTable\n")
        f.write("----------\n")
        if not pass1_result.label_table:
            f.write("<empty>\n")
        else:
            for entry in sorted(pass1_result.label_table.values(), key=lambda e: int(e.address)):
                f.write(
                    f"{entry.name} addr={entry.address} line={entry.line_number}\n"
                )


# -----------------------------------------------------------------------
# .hll writer
# -----------------------------------------------------------------------

def write_hll(
    hll_path: str,
    source_file: str,
    hlx_path: str,
    pass1_result: Pass1Result,
    pass2_result: Pass2Result,
    source_lines: list[str],
    statements,
    source_columns: tuple[int, int] | None = None,
) -> None:
    """Write the Halix assembler listing file (.hll)."""
    with open(hll_path, "w") as f:
        f.write("-----------------------\n")
        f.write("Halix Assembler Listing\n")
        f.write("HASM version 14.0.0 - python Implementation)\n")
        f.write("-----------------------\n")
        f.write("\n")
        f.write(f"Source file: {source_file}\n")
        f.write(f"Listing file: {hll_path}\n")
        f.write(f"Machine code file: {hlx_path}\n")
        f.write("\n")

        instr_map: dict[int, list] = {}
        for instr in pass2_result.instructions:
            instr_map.setdefault(instr.line_number, []).append(instr)
        data_line_map = _build_data_line_map(pass1_result, statements, source_lines)
        statement_map = {st.line_number: st for st in statements}

        for line_num, raw_line in enumerate(source_lines, start=1):
            raw = raw_line.rstrip("\n")
            rendered_source = raw
            if source_columns is not None and line_num in statement_map:
                rendered_source = _render_source_line(
                    statement_map[line_num],
                    raw,
                    source_columns,
                )

            if line_num in instr_map:
                for idx, instr in enumerate(instr_map[line_num]):
                    source_text = rendered_source if idx == 0 else ""
                    f.write(f"{instr.iaddr}  {instr.machine_word}  {source_text}\n")
                continue

            if line_num in data_line_map:
                addr, value = data_line_map[line_num]
                f.write(f"{addr}  {value}  {rendered_source}\n")
                continue

            f.write(f"          {rendered_source}\n")


# -----------------------------------------------------------------------
# Helper
# -----------------------------------------------------------------------

def _build_data_line_map(
    pass1_result: Pass1Result,
    statements,
    source_lines: list[str],
) -> dict[int, tuple[str, str]]:
    """Map data declaration line numbers to their displayed address/value pair."""
    data_line_map: dict[int, tuple[str, str]] = {}

    for st in statements:
        if st.kind != "DIRECTIVE" or st.mnemonic not in {".DATA", ".BLOCK"}:
            continue
        if not st.operands:
            continue

        symbol_name = st.operands[0].upper()
        entry = pass1_result.data_table.get(symbol_name)
        if entry is None:
            continue

        data_line_map[st.line_number] = (entry.address, entry.value)

    return data_line_map


def _render_source_line(statement, raw_line: str, source_columns: tuple[int, int]) -> str:
    """Render the source portion of a listing line using fixed label/mnemonic columns."""
    if statement.kind == "BLANK":
        return raw_line

    label_width, mnemonic_width = source_columns
    code_part, comment_part = _split_comment(raw_line)

    label_text = ""
    mnemonic_text = ""
    operand_text = ""

    if statement.kind == "INSTRUCTION":
        if statement.label is not None:
            label_text = f"{statement.label}:"
        mnemonic_text = statement.mnemonic or ""
        operand_text = _join_operand_tokens(statement.operands)
    elif statement.kind == "DIRECTIVE":
        mnemonic_text = statement.mnemonic or ""
        operands = list(statement.operands)
        if statement.mnemonic in {".DATA", ".BLOCK"} and operands:
            label_text = operands[0]
            operands = operands[1:]
        elif statement.label is not None:
            label_text = f"{statement.label}:"
        operand_text = _join_operand_tokens(operands)

    rendered = f"{label_text:<{label_width}}{mnemonic_text:<{mnemonic_width}}"
    if operand_text:
        rendered = f"{rendered}{operand_text}"
    rendered = rendered.rstrip()

    if comment_part:
        if rendered:
            return f"{rendered}  {comment_part}"
        return comment_part

    if rendered:
        return rendered
    return code_part.rstrip()


def _split_comment(raw_line: str) -> tuple[str, str]:
    comment_index = raw_line.find("#")
    if comment_index < 0:
        return raw_line, ""
    return raw_line[:comment_index].rstrip(), raw_line[comment_index:].rstrip()


def _join_operand_tokens(tokens: list[str]) -> str:
    if not tokens:
        return ""

    parts: list[str] = []
    for token in tokens:
        if token == ",":
            if parts:
                parts[-1] = parts[-1].rstrip() + ","
            else:
                parts.append(",")
            continue
        if token == "=":
            if parts:
                parts[-1] = parts[-1].rstrip() + "="
            else:
                parts.append("=")
            continue
        if parts and not parts[-1].endswith(("=", ",")):
            parts.append(" " + token)
        else:
            parts.append(token)
    return "".join(parts).strip()
