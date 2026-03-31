"""
services/pass1.py
-----------------
Pass 1 of the Halix assembler.

Responsibilities (per SDD-HLX-002 Section 3.3):
  Sub-pass 1a: Build DataTable from .ALLOC, .DATA, and .BLOCK directives.
  Sub-pass 1b: Build LabelTable and track instruction addresses between
               .BEGIN and .END.

SCRUM-22: Opcode table is loaded externally and passed in via HASM_CLI.py.
SCRUM-24: .BLOCK directive allocates contiguous data memory addresses.

No hard-coded opcodes. All instruction recognition is via the
opcode table loaded dynamically from halix_v25.opcode.
"""

from dataclasses import dataclass, field
from typing import Optional

from services.parser import Statement, parse_literal_indexed_symbol

HALIX_MEMORY_LIMIT = 100


# -----------------------------------------------------------------------
# Data structures (per SDD Section 3.3)
# -----------------------------------------------------------------------

@dataclass
class DataEntry:
    name: str           # variable name e.g. 'X'
    address: str        # zero-padded 2-digit string e.g. '00', '07'
    value: str          # zero-padded 4-digit initial value e.g. '0005', '9999'
    size: int = 1       # 1 for .DATA, N for .BLOCK
    values: list[str] = field(default_factory=list)  # multi-value for .BLOCK


@dataclass
class LabelEntry:
    name: str           # label name e.g. 'LOOP'
    address: str        # zero-padded 2-digit instruction address e.g. '04'
    line_number: int    # source line where label is defined


@dataclass
class Pass1Result:
    data_table:     dict[str, DataEntry]  = field(default_factory=dict)
    label_table:    dict[str, LabelEntry] = field(default_factory=dict)
    line_to_iaddr:  dict[int, str]        = field(default_factory=dict)
    code_size:      int = 0
    data_size:      int = 0
    warnings:       list[str] = field(default_factory=list)
    errors:         list["Pass1Error"] = field(default_factory=list)


class Pass1Error(Exception):
    """Raised on fatal Pass 1 errors."""
    def __init__(self, message: str, *, line: int = 0, code: str = "E007"):
        self.code = code
        self.line = line
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _zero_pad_addr(n: int) -> str:
    """Return zero-padded 2-digit address string."""
    return str(n).zfill(2)


def _zero_pad_value(v: int) -> str:
    """Return zero-padded 4-digit data value string."""
    return str(v).zfill(4)


def _parse_value(raw: str) -> int:
    """
    Parse a data value token. Strips leading '=' if present.
    Returns integer. Defaults to 9999 on failure (legacy behavior).
    """
    s = raw.lstrip("=").strip()
    if s.isdigit():
        return int(s)
    return 9999


def _resolve_data_address(entry: DataEntry, offset: int = 0) -> str:
    return _zero_pad_addr(int(entry.address) + offset)


# -----------------------------------------------------------------------
# Sub-pass 1a — Data Table
# -----------------------------------------------------------------------

def _build_data_table(
    statements: list[Statement],
) -> tuple[dict[str, DataEntry], int, list[str], list[Pass1Error]]:
    """
    Scan all .ALLOC, .DATA, and .BLOCK directives to build the data table.

    Returns:
        data_table: dict mapping variable name -> DataEntry
        data_size:  total allocated data memory size
        warnings:   list of non-fatal warning strings
    """
    data_table: dict[str, DataEntry] = {}
    warnings: list[str] = []
    errors: list[Pass1Error] = []
    d_size = 10          # default per legacy assembler
    d_addr = 0
    alloc_line = 0

    for st in statements:
        if st.kind != "DIRECTIVE":
            continue

        # ── .ALLOC ─────────────────────────────────────────────────────
        if st.mnemonic == ".ALLOC":
            if st.operands and st.operands[0].isdigit():
                d_size = int(st.operands[0])
                alloc_line = st.line_number
                if d_size > HALIX_MEMORY_LIMIT:
                    errors.append(
                        Pass1Error(
                            f".ALLOC value {d_size} exceeds Halix data memory limit 99.",
                            line=st.line_number,
                            code="E032",
                        )
                    )
            continue

        # ── .DATA ──────────────────────────────────────────────────────
        if st.mnemonic == ".DATA":
            if not st.operands:
                errors.append(
                    Pass1Error(
                        ".DATA directive missing variable name.",
                        line=st.line_number,
                    )
                )
                continue

            var_name = st.operands[0].upper()
            indexed_target = parse_literal_indexed_symbol(var_name)

            if indexed_target is not None:
                base_name, element_index = indexed_target
                block_entry = data_table.get(base_name)
                if block_entry is None:
                    errors.append(
                        Pass1Error(
                            f"indexed assignment target '{var_name}' refers to undefined block '{base_name}'.",
                            line=st.line_number,
                        )
                    )
                    continue
                if block_entry.size <= 1:
                    errors.append(
                        Pass1Error(
                            f"indexed assignment target '{var_name}' refers to non-block symbol '{base_name}'.",
                            line=st.line_number,
                        )
                    )
                    continue
                if element_index >= block_entry.size:
                    errors.append(
                        Pass1Error(
                            f"indexed assignment target '{var_name}' exceeds block '{base_name}' size {block_entry.size}.",
                            line=st.line_number,
                        )
                    )
                    continue

                raw_value = 9999
                if len(st.operands) == 3 and st.operands[1] == "=":
                    raw_value = _parse_value(st.operands[2])
                elif len(st.operands) == 2 and st.operands[1].startswith("="):
                    raw_value = _parse_value(st.operands[1])

                block_entry.values[element_index] = _zero_pad_value(raw_value)
                if element_index == 0:
                    block_entry.value = block_entry.values[0]
                continue

            if var_name in data_table:
                errors.append(
                    Pass1Error(
                        f"duplicate variable '{var_name}' previously defined earlier in the data section.",
                        line=st.line_number,
                    )
                )
                continue

            if d_addr >= HALIX_MEMORY_LIMIT:
                errors.append(
                    Pass1Error(
                        "data memory limit exceeded. Halix data addresses range from 00 to 99.",
                        line=st.line_number,
                        code="E032",
                    )
                )
                continue

            # Extract initial value: .DATA X = 5  or  .DATA X =5  or  .DATA X
            raw_value = 9999
            if len(st.operands) == 3 and st.operands[1] == "=":
                raw_value = _parse_value(st.operands[2])
            elif len(st.operands) == 2 and st.operands[1].startswith("="):
                raw_value = _parse_value(st.operands[1])

            entry = DataEntry(
                name=var_name,
                address=_zero_pad_addr(d_addr),
                value=_zero_pad_value(raw_value),
                size=1,
                values=[_zero_pad_value(raw_value)],
            )
            data_table[var_name] = entry
            d_addr += 1
            continue

        # ── .BLOCK (SCRUM-24) ──────────────────────────────────────────
        if st.mnemonic == ".BLOCK":
            # Supported forms:
            #   .BLOCK <name> <size>
            #   .BLOCK <name> =v1,=v2,...
            if len(st.operands) < 2:
                errors.append(
                    Pass1Error(
                        ".BLOCK missing name or size.",
                        line=st.line_number,
                    )
                )
                continue

            block_name = st.operands[0].upper()
            init_values: list[str] = []

            if st.operands[1].isdigit():
                block_size = int(st.operands[1])
                while len(init_values) < block_size:
                    init_values.append("9999")
            else:
                for tok in st.operands[1:]:
                    if tok == ",":
                        continue
                    clean = tok.lstrip("=").strip()
                    if not clean.isdigit():
                        errors.append(
                            Pass1Error(
                                f".BLOCK initializer value '{tok}' is not numeric.",
                                line=st.line_number,
                            )
                        )
                        continue
                    init_values.append(_zero_pad_value(int(clean)))

                block_size = len(init_values)
                if block_size == 0:
                    errors.append(
                        Pass1Error(
                            ".BLOCK initializer requires at least one value.",
                            line=st.line_number,
                        )
                    )
                    continue

            if block_name in data_table:
                errors.append(
                    Pass1Error(
                        f"duplicate block '{block_name}' previously defined earlier in the data section.",
                        line=st.line_number,
                    )
                )
                continue

            if d_addr + block_size > HALIX_MEMORY_LIMIT:
                errors.append(
                    Pass1Error(
                        f".BLOCK '{block_name}' with size {block_size} exceeds Halix data memory limit 99.",
                        line=st.line_number,
                        code="E032",
                    )
                )
                continue

            # Allocate block_size consecutive addresses.
            # Block name maps to the FIRST address (base address).
            entry = DataEntry(
                name=block_name,
                address=_zero_pad_addr(d_addr),
                value=init_values[0],
                size=block_size,
                values=init_values,
            )
            data_table[block_name] = entry
            d_addr += block_size
            continue

    if d_addr > d_size:
        errors.append(
            Pass1Error(
                f".ALLOC value {d_size} is too small for allocated data cells {d_addr}.",
                line=alloc_line,
            )
        )

    return data_table, d_size, warnings, errors


# -----------------------------------------------------------------------
# Sub-pass 1b — Label Table + Location Counter
# -----------------------------------------------------------------------

def _build_label_table(
    statements: list[Statement],
) -> tuple[dict[str, LabelEntry], dict[int, str], int, list[str], list[Pass1Error]]:
    """
    Scan executable statements between .BEGIN and .END.
    Build the label table and track instruction addresses.

    Returns:
        label_table:    dict mapping label name -> LabelEntry
        line_to_iaddr:  dict mapping source line number -> instruction address
        code_size:      total number of instructions
        warnings:       list of non-fatal warning strings
    """
    label_table: dict[str, LabelEntry] = {}
    line_to_iaddr: dict[int, str] = {}
    warnings: list[str] = []
    errors: list[Pass1Error] = []

    # Find .BEGIN and .END line numbers from the statement list
    begin_line: Optional[int] = None
    end_line: Optional[int] = None

    for st in statements:
        if st.kind == "DIRECTIVE":
            if st.mnemonic == ".BEGIN" and begin_line is None:
                begin_line = st.line_number
            if st.mnemonic == ".END":
                end_line = st.line_number  # last .END wins

    if begin_line is None:
        errors.append(Pass1Error("No .BEGIN directive found during Pass 1."))
    if end_line is None:
        errors.append(Pass1Error("No .END directive found during Pass 1."))
    if errors:
        return label_table, line_to_iaddr, 0, warnings, errors

    i_addr = 0

    for st in statements:
        # Only process lines strictly between .BEGIN and .END
        if st.line_number <= begin_line or st.line_number >= end_line:
            continue

        # Skip blank lines and comment-only lines — no address increment
        if st.kind == "BLANK":
            continue

        # Skip directive lines inside code section — no address increment
        if st.kind == "DIRECTIVE":
            continue

        # Record label if present — label gets current address
        if i_addr >= HALIX_MEMORY_LIMIT:
            errors.append(
                Pass1Error(
                    "instruction memory limit exceeded. Halix instruction addresses range from 00 to 99.",
                    line=st.line_number,
                    code="E031",
                )
            )
            break

        if st.label is not None:
            label_name = st.label.upper()
            if label_name in label_table:
                first_line = label_table[label_name].line_number
                errors.append(
                    Pass1Error(
                        f"duplicate label '{label_name}' previously defined at line {first_line}.",
                        line=st.line_number,
                    )
                )
            else:
                label_table[label_name] = LabelEntry(
                    name=label_name,
                    address=_zero_pad_addr(i_addr),
                    line_number=st.line_number,
                )

        # Record instruction address for this line
        line_to_iaddr[st.line_number] = _zero_pad_addr(i_addr)
        i_addr += 1

    return label_table, line_to_iaddr, i_addr, warnings, errors


# -----------------------------------------------------------------------
# Public entry point
# -----------------------------------------------------------------------

def run_pass1(statements: list[Statement]) -> Pass1Result:
    """
    Run Pass 1 on the parsed statement list.

    Args:
        statements: output of parse_tokens() from parser.py

    Returns:
        Pass1Result with data_table, label_table, line_to_iaddr,
        code_size, data_size, and warnings.

    Raises:
        Pass1Error on fatal structural errors.
    """
    result = Pass1Result()

    # Sub-pass 1a: data and block table
    data_table, data_size, data_warnings, data_errors = _build_data_table(statements)
    result.data_table = data_table
    result.data_size = data_size
    result.warnings.extend(data_warnings)
    result.errors.extend(data_errors)

    # Sub-pass 1b: label table and location counter
    label_table, line_to_iaddr, code_size, label_warnings, label_errors = _build_label_table(statements)
    result.label_table = label_table
    result.line_to_iaddr = line_to_iaddr
    result.code_size = code_size
    result.warnings.extend(label_warnings)
    result.errors.extend(label_errors)

    return result
