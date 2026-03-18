"""
services/pass2.py
-----------------
Pass 2 / Encoder for the Halix assembler.

Responsibilities (per SDD-HLX-002 Section 3.5):
  - Second scan of statements between .BEGIN and .END.
  - Looks up each mnemonic in the opcode table (no hard-coded opcodes).
  - Determines operand group from OpcodeEntry.operand_type.
  - Builds a 4-digit machine word string for each instruction.
  - Reports errors for undefined variables, undefined labels,
    bad immediate values, and unknown mnemonics.

Machine word format (SDD Section 3.5.1):
  Digits [3-2] = opcode (2 decimal digits)
  Digits [1-0] = operand (2 decimal digits)
  Example: LOAD X where X is at data address 03 -> '0303'

SCRUM-23: FR-GEN-001, FR-GEN-005
"""

from dataclasses import dataclass, field
from typing import Optional

from services.parser import Statement
from services.pass1 import Pass1Result, DataEntry, LabelEntry
from services.HASM_opcode_Loader import OpcodeTable, OPERAND_NONE, OPERAND_BRANCH, OPERAND_IMMEDIATE, OPERAND_DATA


# -----------------------------------------------------------------------
# Data structures
# -----------------------------------------------------------------------

@dataclass
class EncodedInstruction:
    line_number: int
    iaddr: str          # zero-padded 2-digit instruction address
    machine_word: str   # 4-digit machine word string e.g. '0302'
    source_text: str    # original source line text for listing


@dataclass
class Pass2Result:
    instructions: list[EncodedInstruction] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class Pass2Error(Exception):
    pass


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _zero_pad(n: int) -> str:
    return str(n).zfill(2)


# -----------------------------------------------------------------------
# Public entry point
# -----------------------------------------------------------------------

def run_pass2(
    statements: list[Statement],
    pass1_result: Pass1Result,
    opcode_table: OpcodeTable,
    source_lines: list[str],
) -> Pass2Result:
    """
    Encode all instructions between .BEGIN and .END into 4-digit
    machine words.

    Args:
        statements:    output of parse_tokens()
        pass1_result:  output of run_pass1() — data_table + label_table
        opcode_table:  loaded OpcodeTable from HASM_opcode_Loader
        source_lines:  raw source lines (for listing file annotations)

    Returns:
        Pass2Result with encoded instructions and any errors/warnings.
    """
    result = Pass2Result()
    data_table = pass1_result.data_table
    label_table = pass1_result.label_table

    # Locate .BEGIN and .END boundaries
    begin_line: Optional[int] = None
    end_line: Optional[int] = None
    for st in statements:
        if st.kind == "DIRECTIVE":
            if st.mnemonic == ".BEGIN" and begin_line is None:
                begin_line = st.line_number
            if st.mnemonic == ".END":
                end_line = st.line_number

    if begin_line is None or end_line is None:
        raise Pass2Error("FATAL: .BEGIN or .END not found during Pass 2.")

    i_addr = 0

    for st in statements:
        # Only process lines strictly between .BEGIN and .END
        if st.line_number <= begin_line or st.line_number >= end_line:
            continue

        # Skip blank lines — no output, no address increment
        if st.kind == "BLANK":
            continue

        # Skip directive lines inside code section — no output, no increment
        if st.kind == "DIRECTIVE":
            continue

        # Get raw source line text for listing (strip newline)
        raw_line = source_lines[st.line_number - 1].rstrip() if st.line_number <= len(source_lines) else ""

        mnemonic = st.mnemonic
        if mnemonic is None:
            result.errors.append(
                f"Line {st.line_number}: instruction has no mnemonic — skipped."
            )
            i_addr += 1
            continue

        # Look up opcode — NO hard-coded opcode numbers
        entry = opcode_table.lookup(mnemonic)
        if entry is None:
            result.errors.append(
                f"ERROR E010 Line {st.line_number}: "
                f"unknown mnemonic '{mnemonic}' — opcode 00 used."
            )
            machine_word = "0000"
            result.instructions.append(EncodedInstruction(
                line_number=st.line_number,
                iaddr=_zero_pad(i_addr),
                machine_word=machine_word,
                source_text=raw_line,
            ))
            i_addr += 1
            continue

        opcode = entry.numeric          # e.g. "03"
        operand_type = entry.operand_type
        operands = st.operands          # list of operand strings from parser

        # ── Group: no operand ─────────────────────────────────────────
        if operand_type == OPERAND_NONE:
            machine_word = opcode + "00"

        # ── Group: branch (label address) ─────────────────────────────
        elif operand_type == OPERAND_BRANCH:
            if not operands:
                result.errors.append(
                    f"ERROR E025 Line {st.line_number}: "
                    f"'{mnemonic}' requires a label operand — addr 99 used."
                )
                machine_word = opcode + "99"
            else:
                label_name = operands[0].upper()
                label_entry = label_table.get(label_name)
                if label_entry is None:
                    result.errors.append(
                        f"ERROR E021 Line {st.line_number}: "
                        f"undefined label '{label_name}' "
                    )
                    machine_word = opcode + "99"
                else:
                    machine_word = opcode + label_entry.address

        # ── Group: immediate (=NN) ─────────────────────────────────────
        elif operand_type == OPERAND_IMMEDIATE:
            if not operands:
                result.errors.append(
                    f"ERROR E022 Line {st.line_number}: "
                    f"'{mnemonic}' requires an immediate operand — value 00 used."
                )
                machine_word = opcode + "00"
            else:
                raw_op = operands[0]
                # Strip leading '=' — parser guarantees this format
                val_str = raw_op.lstrip("=").strip()
                if not val_str.isdigit():
                    result.errors.append(
                        f"ERROR E023 Line {st.line_number}: "
                        f"immediate value '{raw_op}' is not numeric — value 00 used."
                    )
                    machine_word = opcode + "00"
                else:
                    ival = int(val_str)
                    if ival > 99:
                        result.warnings.append(
                            f"WARNING Line {st.line_number}: "
                            f"immediate value {ival} exceeds 2 digits — truncated."
                        )
                        ival = ival % 100
                    machine_word = opcode + _zero_pad(ival)

        # ── Group: data address (variable name) ───────────────────────
        else:  # OPERAND_DATA
            if not operands:
                result.errors.append(
                    f"ERROR E026 Line {st.line_number}: "
                    f"'{mnemonic}' requires a data operand — addr 99 used."
                )
                machine_word = opcode + "99"
            else:
                var_name = operands[0].upper()
                data_entry = data_table.get(var_name)
                if data_entry is None:
                    result.errors.append(
                        f"ERROR E030 Line {st.line_number}: "
                        f"undefined variable '{var_name}' — addr 99 used."
                    )
                    machine_word = opcode + "99"
                else:
                    machine_word = opcode + data_entry.address

        result.instructions.append(EncodedInstruction(
            line_number=st.line_number,
            iaddr=_zero_pad(i_addr),
            machine_word=machine_word,
            source_text=raw_line,
        ))
        i_addr += 1

    return result
