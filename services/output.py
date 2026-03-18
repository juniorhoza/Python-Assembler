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

        instr_map = {instr.line_number: instr for instr in pass2_result.instructions}
        data_line_map = _build_data_line_map(pass1_result, statements, source_lines)

        for line_num, raw_line in enumerate(source_lines, start=1):
            raw = raw_line.rstrip("\n")

            if line_num in instr_map:
                instr = instr_map[line_num]
                f.write(f"{instr.iaddr}  {instr.machine_word}  {raw}\n")
                continue

            if line_num in data_line_map:
                addr, value = data_line_map[line_num]
                f.write(f"{addr}  {value}  {raw}\n")
                continue

            f.write(f"          {raw}\n")


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
