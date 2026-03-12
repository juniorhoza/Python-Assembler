"""
hasm_opcode_loader.py
----------------------
Dynamically loads and classifies the Halix opcode table from the
halix_v25.opcode file at runtime.

CLIENT REQUIREMENT: No hard-coded opcodes in assembler logic.
Adding new instructions requires only updating halix_v25.opcode
for opcode numbers. Operand grouping is now static (design-document groups).

Opcode file format (confirmed from halix_v25.opcode):
    00 #NOOP#
    01 #READ#
    ...
    99 #HALT#

"""

import os
from dataclasses import dataclass, field
from typing import Optional

# Operand type constants — used by pass-2 encoder
OPERAND_NONE      = "none"        # instruction takes no operand (00 used)
OPERAND_BRANCH    = "branch"      # operand is an instruction label address
OPERAND_IMMEDIATE = "immediate"   # operand is an immediate value (=NN form)
OPERAND_DATA      = "data"        # operand is a data memory address (default)

# Static instruction grouping from design document section 3.4.1
NO_OPERAND_MNEMONICS = {
    "NOOP", "CLEAR", "SET", "INCR", "DECR", "SHACC", "RET", "SHINDX",
    "ICLR", "IREAD", "IWRITE", "ILOAD", "ISTORE", "IINCR", "IDECR",
    "IADD", "ISUB", "IMULT", "IDIV", "IMOD", "ICLT", "ICLE", "ICEQ",
    "ICNE", "ICGE", "ICGT", "SHBASE", "MOVEB", "MOVEA", "IMOVEA", "HALT",
}
BRANCH_MNEMONICS = {"BRANCH", "BRT", "BRF", "BSUB"}
IMMEDIATE_MNEMONICS = {"SETI", "ADDI", "SUBI", "MULTI", "DIVI", "MODI"}


@dataclass
class OpcodeEntry:
    numeric: str        # zero-padded two-digit string, e.g. "03"
    mnemonic: str       # e.g. "LOAD"
    operand_type: str   # one of the OPERAND_* constants above


@dataclass
class OpcodeTable:
    # Primary lookup: mnemonic -> OpcodeEntry
    by_mnemonic: dict[str, OpcodeEntry] = field(default_factory=dict)
    # Reverse lookup: numeric string -> OpcodeEntry
    by_numeric: dict[str, OpcodeEntry] = field(default_factory=dict)

    def lookup(self, mnemonic: str) -> Optional[OpcodeEntry]:
        return self.by_mnemonic.get(mnemonic.upper())

    def is_valid(self, mnemonic: str) -> bool:
        return mnemonic.upper() in self.by_mnemonic


# -----------------------------------------------------------------------
# Opcode file parser
# -----------------------------------------------------------------------

def _parse_opcode_file(opcode_path: str) -> dict[str, str]:
    """
    Parse halix_v25.opcode into {mnemonic: numeric_string}.
    Confirmed file format: '00 #NOOP#'  (numeric space #MNEMONIC#)
    Skips blank lines and comment lines.
    """
    mnemonic_to_numeric = {}
    with open(opcode_path, "r") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                print(f"WARNING: Malformed opcode entry at line {lineno}: '{line}' — skipped.")
                continue
            numeric = parts[0].zfill(2)
            # Strip the # delimiters that the legacy assembler uses
            mnemonic = parts[1].replace("#", "").strip().upper()
            if mnemonic in mnemonic_to_numeric:
                print(f"WARNING: Duplicate mnemonic '{mnemonic}' at line {lineno} — first entry kept.")
                continue
            mnemonic_to_numeric[mnemonic] = numeric
    return mnemonic_to_numeric


def _operand_type_for_mnemonic(mnemonic: str) -> str:
    m = mnemonic.upper()
    if m in NO_OPERAND_MNEMONICS:
        return OPERAND_NONE
    if m in BRANCH_MNEMONICS:
        return OPERAND_BRANCH
    if m in IMMEDIATE_MNEMONICS:
        return OPERAND_IMMEDIATE
    return OPERAND_DATA


# -----------------------------------------------------------------------
# Public loader
# -----------------------------------------------------------------------

def load_opcode_table(opcode_path: str) -> OpcodeTable:
    """
    Load the opcode table dynamically from halix_v25.opcode.

    Args:
        opcode_path: Path to halix_v25.opcode
    Returns:
        A fully populated OpcodeTable ready for use by pass-1 and pass-2.

    Raises:
        FileNotFoundError if opcode_path does not exist.
        ValueError if opcode_path is empty or unparseable.
    """
    if not os.path.isfile(opcode_path):
        raise FileNotFoundError(
            f"FATAL: Opcode table file '{opcode_path}' not found. "
            f"Expected in Halix_Software/."
        )

    mnemonic_to_numeric = _parse_opcode_file(opcode_path)
    if not mnemonic_to_numeric:
        raise ValueError(
            f"FATAL: Opcode table file '{opcode_path}' produced no valid entries."
        )

    table = OpcodeTable()
    for mnemonic, numeric in mnemonic_to_numeric.items():
        operand_type = _operand_type_for_mnemonic(mnemonic)
        entry = OpcodeEntry(
            numeric=numeric,
            mnemonic=mnemonic,
            operand_type=operand_type
        )
        table.by_mnemonic[mnemonic] = entry
        table.by_numeric[numeric] = entry

    print(f"Opcode table loaded: {len(table.by_mnemonic)} instructions from '{opcode_path}'.")
    return table
