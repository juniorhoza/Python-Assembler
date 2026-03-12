"""
pass1.py
--------
Builds the data symbol table and label table from parsed statements.
"""

from dataclasses import dataclass, field

from services.parser import (
    Statement,
    BRANCH_MNEMONICS,
    IMMEDIATE_MNEMONICS,
    NO_OPERAND_MNEMONICS,
)


@dataclass
class DataEntry:
    name: str
    address: str
    value: str
    size: int = 1
    values: list[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class LabelEntry:
    name: str
    address: str
    line_number: int = 0


@dataclass
class Pass1Result:
    data_table: dict[str, DataEntry] = field(default_factory=dict)
    label_table: dict[str, LabelEntry] = field(default_factory=dict)
    data_size: int = 10
    code_size: int = 0
    line_to_iaddr: dict[int, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class Pass1Error(Exception):
    def __init__(self, line: int, message: str):
        self.line = line
        self.message = message
        super().__init__(str(self))

    def __str__(self) -> str:
        return f"Pass1 Error at line {self.line}: {self.message}"


def _z2(value: int) -> str:
    return str(value).zfill(2)


def _z4(value: int) -> str:
    return str(value).zfill(4)


def _extract_data_value(operands: list[str]) -> str:
    if len(operands) == 1:
        return "9999"
    if len(operands) >= 2 and operands[1].startswith("=") and len(operands[1]) > 1:
        return _z4(int(operands[1][1:]))
    if len(operands) >= 3 and operands[1] == "=":
        return _z4(int(operands[2]))
    return "9999"


def _extract_block_values(operands: list[str], block_size: int) -> list[str]:
    values: list[int] = []
    init_tokens = operands[2:]
    if not init_tokens:
        return ["0000"] * block_size

    idx = 0
    if init_tokens[0] == "=":
        idx = 1
    elif init_tokens[0].startswith("="):
        values.append(int(init_tokens[0][1:]))
        idx = 1

    expect_value = True if idx < len(init_tokens) else False
    while idx < len(init_tokens):
        token = init_tokens[idx]
        if expect_value:
            if token.startswith("="):
                values.append(int(token[1:]))
            else:
                values.append(int(token))
            expect_value = False
        else:
            if token != ",":
                raise ValueError(f"invalid block initializer token '{token}'")
            expect_value = True
        idx += 1

    padded = [_z4(v) for v in values]
    while len(padded) < block_size:
        padded.append("0000")
    return padded


def _record_data_symbol(result: Pass1Result, entry: DataEntry) -> None:
    if entry.name in result.data_table:
        prev = result.data_table[entry.name]
        raise Pass1Error(entry.line_number, f"duplicate data symbol '{entry.name}' previously defined at line {prev.line_number}")
    result.data_table[entry.name] = entry


def _record_label(label_table: dict[str, LabelEntry], st: Statement, iaddr: int) -> None:
    name = st.label.upper()
    if name in label_table:
        raise Pass1Error(st.line_number, f"duplicate label '{name}' previously defined at line {label_table[name].line_number}")
    label_table[name] = LabelEntry(name=name, address=_z2(iaddr), line_number=st.line_number)


def build_data_table(statements: list[Statement]) -> tuple[dict[str, DataEntry], int]:
    result = Pass1Result()
    daddr = 0
    alloc_line = 0
    explicit_alloc = False

    for st in statements:
        if st.kind != "DIRECTIVE" or st.mnemonic is None:
            continue

        if st.mnemonic == ".ALLOC":
            result.data_size = int(st.operands[0])
            alloc_line = st.line_number
            explicit_alloc = True
            continue

        if st.mnemonic == ".DATA":
            name = st.operands[0].upper()
            try:
                data_value = _extract_data_value(st.operands)
            except ValueError as exc:
                raise Pass1Error(st.line_number, f"invalid .DATA initializer for '{name}': {exc}") from exc
            entry = DataEntry(
                name=name,
                address=_z2(daddr),
                value=data_value,
                size=1,
                values=[data_value],
                line_number=st.line_number,
            )
            _record_data_symbol(result, entry)
            daddr += 1
            continue

        if st.mnemonic == ".BLOCK":
            name = st.operands[0].upper()
            block_size = int(st.operands[1])
            try:
                block_values = _extract_block_values(st.operands, block_size)
            except ValueError as exc:
                raise Pass1Error(st.line_number, f"invalid .BLOCK initializer for '{name}': {exc}") from exc
            entry = DataEntry(
                name=name,
                address=_z2(daddr),
                value=block_values[0],
                size=block_size,
                values=block_values,
                line_number=st.line_number,
            )
            _record_data_symbol(result, entry)
            daddr += block_size

    if explicit_alloc and daddr > result.data_size:
        raise Pass1Error(
            alloc_line,
            f".ALLOC value {result.data_size} is too small for allocated data cells {daddr}",
        )

    if not explicit_alloc and daddr > result.data_size:
        result.data_size = daddr

    return result.data_table, result.data_size


def build_label_table(statements: list[Statement]) -> tuple[dict[str, LabelEntry], dict[int, str], int]:
    label_table: dict[str, LabelEntry] = {}
    line_to_iaddr: dict[int, str] = {}

    begin_idx = next((i for i, st in enumerate(statements) if st.kind == "DIRECTIVE" and st.mnemonic == ".BEGIN"), None)
    end_idx = max((i for i, st in enumerate(statements) if st.kind == "DIRECTIVE" and st.mnemonic == ".END"), default=-1)
    if begin_idx is None or end_idx < 0:
        return label_table, line_to_iaddr, 0

    iaddr = 0
    for st in statements[begin_idx + 1:end_idx]:
        if st.kind == "BLANK":
            if st.label:
                _record_label(label_table, st, iaddr)
            continue

        if st.kind == "DIRECTIVE" and st.mnemonic in {".BEGIN", ".END", ".ALLOC"}:
            continue

        if st.label:
            _record_label(label_table, st, iaddr)

        if st.kind == "INSTRUCTION":
            line_to_iaddr[st.line_number] = _z2(iaddr)
            iaddr += 1

    return label_table, line_to_iaddr, iaddr


def validate_symbol_references(statements: list[Statement], result: Pass1Result) -> list[str]:
    warnings: list[str] = []
    begin_idx = next((i for i, st in enumerate(statements) if st.kind == "DIRECTIVE" and st.mnemonic == ".BEGIN"), None)
    end_idx = max((i for i, st in enumerate(statements) if st.kind == "DIRECTIVE" and st.mnemonic == ".END"), default=-1)
    if begin_idx is None or end_idx < 0:
        return warnings

    for st in statements[begin_idx + 1:end_idx]:
        if st.kind != "INSTRUCTION" or st.mnemonic is None:
            continue

        mnemonic = st.mnemonic.upper()
        operands = st.operands
        if not operands:
            continue

        operand = operands[0].upper()
        if mnemonic in NO_OPERAND_MNEMONICS or mnemonic in IMMEDIATE_MNEMONICS:
            continue

        if mnemonic in BRANCH_MNEMONICS:
            if operand not in result.label_table:
                warnings.append(
                    f"E021 line {st.line_number}: Undefined label '{operand}' -- address 99 used"
                )
            continue

        if operand not in result.data_table:
            warnings.append(
                f"E020 line {st.line_number}: Undefined data variable '{operand}' -- address 99 used"
            )

    return warnings


def run_pass1(statements: list[Statement]) -> Pass1Result:
    data_table, data_size = build_data_table(statements)
    label_table, line_to_iaddr, code_size = build_label_table(statements)
    result = Pass1Result(
        data_table=data_table,
        label_table=label_table,
        data_size=data_size,
        code_size=code_size,
        line_to_iaddr=line_to_iaddr,
    )
    result.warnings = validate_symbol_references(statements, result)
    return result
