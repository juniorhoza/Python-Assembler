"""
hasm_opcode_loader.py
----------------------
Dynamically loads and classifies the Halix opcode table from the
halix_v25.opcode file at runtime.

CLIENT REQUIREMENT: No hard-coded opcodes in assembler logic.
Adding new instructions requires only updating halix_v25.opcode
and halix_v25.opcode.cfg — no Python source changes needed.

Opcode file format (confirmed from halix_v25.opcode):
    00 #NOOP#
    01 #READ#
    ...
    99 #HALT#

Operand type config file format (halix_v25.opcode.cfg):
    # Maps operand_type to comma-separated mnemonic list
    none    = NOOP,CLEAR,SET,INCR,DECR,SHACC,RET,SHINDX,...
    branch  = BRANCH,BRT,BRF,BSUB
    immediate = SETI,ADDI,SUBI,MULTI,DIVI,MODI
    # All others default to: data (require data memory address)
"""

import os
from dataclasses import dataclass, field
from typing import Optional

# Operand type constants — used by pass-2 encoder, not hard-coded opcode numbers
OPERAND_NONE      = "none"        # instruction takes no operand (00 used)
OPERAND_BRANCH    = "branch"      # operand is an instruction label address
OPERAND_IMMEDIATE = "immediate"   # operand is an immediate value (=NN form)
OPERAND_DATA      = "data"        # operand is a data memory address (default)


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


def _parse_cfg_file(cfg_path: str) -> dict[str, str]:
    """
    Parse halix_v25.opcode.cfg into {mnemonic: operand_type}.
    Format: operand_type = MNEMONIC1, MNEMONIC2, ...
    Lines starting with # are comments.
    Mnemonics not listed default to OPERAND_DATA.
    """
    mnemonic_to_type = {}
    if not os.path.isfile(cfg_path):
        print(f"WARNING: Opcode config file '{cfg_path}' not found. "
              f"All instructions will default to operand type '{OPERAND_DATA}'.")
        return mnemonic_to_type

    with open(cfg_path, "r") as f:
        for raw in f:
            line = raw.split("#")[0].strip()
            if not line or "=" not in line:
                continue
            operand_type, mnemonics_str = line.split("=", 1)
            operand_type = operand_type.strip().lower()
            for m in mnemonics_str.split(","):
                mnemonic = m.strip().upper()
                if mnemonic:
                    mnemonic_to_type[mnemonic] = operand_type
    return mnemonic_to_type


# -----------------------------------------------------------------------
# Public loader
# -----------------------------------------------------------------------

def load_opcode_table(opcode_path: str, cfg_path: Optional[str] = None) -> OpcodeTable:
    """
    Load the opcode table dynamically from halix_v25.opcode (and optional .cfg).

    Args:
        opcode_path: Path to halix_v25.opcode
        cfg_path:    Path to halix_v25.opcode.cfg (operand type config).
                     If None, defaults to same directory as opcode_path.

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

    # Derive default cfg path if not provided
    if cfg_path is None:
        cfg_path = opcode_path + ".cfg"

    mnemonic_to_numeric = _parse_opcode_file(opcode_path)
    if not mnemonic_to_numeric:
        raise ValueError(
            f"FATAL: Opcode table file '{opcode_path}' produced no valid entries."
        )

    mnemonic_to_type = _parse_cfg_file(cfg_path)

    table = OpcodeTable()
    for mnemonic, numeric in mnemonic_to_numeric.items():
        operand_type = mnemonic_to_type.get(mnemonic, OPERAND_DATA)
        entry = OpcodeEntry(
            numeric=numeric,
            mnemonic=mnemonic,
            operand_type=operand_type
        )
        table.by_mnemonic[mnemonic] = entry
        table.by_numeric[numeric] = entry

    print(f"Opcode table loaded: {len(table.by_mnemonic)} instructions from '{opcode_path}'.")
    return table