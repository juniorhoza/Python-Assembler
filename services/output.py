"""
services/output.py
------------------
Writes the .hlx machine code file and .hll listing file.

Output formats (per SDD-HLX-002 Section 2.4):

.hlx format:
  Line 1:       NN          (2-digit code size)
  Lines 2..N+1: XXYY        (one 4-digit machine word per instruction)
  Line N+2:     MM          (2-digit data memory size)
  Lines N+3+:   VVVV        (one 4-digit data value per variable, in address order)

.hll listing format:
  Data section:   addr  value  source_line
  Code section:   iaddr  machine_word  source_line

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
    """
    Write the Halix assembler listing file (.hll).
    Shows data declarations then code section with addresses and
    machine words alongside original source lines.
    """
    with open(hll_path, "w") as f:

        # Header
        f.write("-----------------------\n")
        f.write("Halix Assembler Listing\n")
        f.write("  (Python Assembler)\n")
        f.write("-----------------------\n")
        f.write("\n")
        f.write(f"Source file:  {source_file}\n")
        f.write(f"Listing file: {hll_path}\n")
        f.write(f"Machine code: {hlx_path}\n")
        f.write("\n")

        # Data section — addr  value  source line
        f.write("-- DATA --\n")
        sorted_data = sorted(
            pass1_result.data_table.values(),
            key=lambda e: int(e.address)
        )
        for entry in sorted_data:
            if entry.size == 1:
                # Find the original source line for this variable
                src = _find_data_source_line(entry.name, statements, source_lines)
                f.write(f"{entry.address}  {entry.value}  {src}\n")
            else:
                # .BLOCK — show each slot
                for i, val in enumerate(entry.values):
                    addr = str(int(entry.address) + i).zfill(2)
                    label = f"{entry.name}[{i}]" if i > 0 else entry.name
                    src = _find_data_source_line(entry.name, statements, source_lines) if i == 0 else ""
                    f.write(f"{addr}  {val}  {label}  {src}\n")

        f.write("\n")

        # Code section — iaddr  machine_word  source line
        f.write("-- CODE --\n")
        instr_map = {instr.line_number: instr for instr in pass2_result.instructions}

        for st in statements:
            line_num = st.line_number
            raw = source_lines[line_num - 1].rstrip() if line_num <= len(source_lines) else ""

            if line_num in instr_map:
                instr = instr_map[line_num]
                f.write(f"{instr.iaddr}  {instr.machine_word}  {raw}\n")
            else:
                # Directive, blank, or comment line — show without address/word
                f.write(f"          {raw}\n")

        f.write("\n")
        f.write("-- END OF LISTING --\n")


# -----------------------------------------------------------------------
# Helper
# -----------------------------------------------------------------------

def _find_data_source_line(var_name: str, statements, source_lines: list[str]) -> str:
    """Find the original source line text for a .DATA or .BLOCK declaration."""
    for st in statements:
        if st.kind == "DIRECTIVE" and st.mnemonic in {".DATA", ".BLOCK"}:
            if st.operands and st.operands[0].upper() == var_name.upper():
                ln = st.line_number
                if ln <= len(source_lines):
                    return source_lines[ln - 1].rstrip()
    return ""