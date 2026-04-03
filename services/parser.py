"""
parser.py
---------
Builds Statement objects from the flat lexer token stream.
"""

from dataclasses import dataclass, field
import re
from collections import defaultdict

from services.lexer import Token


@dataclass
class Statement:
    line_number: int
    label: str | None
    kind: str
    mnemonic: str | None
    operands: list[str] = field(default_factory=list)


class ParserError(Exception):
    def __init__(self, line: int, message: str, column: int | None = None, code: str = "E006"):
        self.code = code
        self.line = line
        self.message = message
        self.column = column
        super().__init__(str(self))

    def __str__(self) -> str:
        if self.column is None:
            return self.message
        return f"{self.message} at column {self.column}"


_IDENT_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_INDEXED_IDENT_RE = re.compile(r"^([A-Z_][A-Z0-9_]*)\[(\d+|[A-Z_][A-Z0-9_]*)\]$")
_DIRECTIVES = {".ALLOC", ".DATA", ".BLOCK", ".BEGIN", ".END"}

# ISA operand groups from design document section 3.4.1
NO_OPERAND_MNEMONICS = {
    "NOOP", "CLEAR", "SET", "INCR", "DECR", "SHACC", "RET", "SHINDX",
    "ICLR", "IREAD", "IWRITE", "ILOAD", "ISTORE", "IINCR", "IDECR",
    "IADD", "ISUB", "IMULT", "IDIV", "IMOD", "ICLT", "ICLE", "ICEQ",
    "ICNE", "ICGE", "ICGT", "SHBASE", "MOVEB", "MOVEA", "IMOVEA", "HALT",
}
BRANCH_MNEMONICS = {"BRANCH", "BRT", "BRF", "BSUB"}
IMMEDIATE_MNEMONICS = {"SETI", "ADDI", "SUBI", "MULTI", "DIVI", "MODI"}
INDIRECT_MNEMONIC_MAP = {
    "READ": "IREAD",
    "WRITE": "IWRITE",
    "LOAD": "ILOAD",
    "STORE": "ISTORE",
    "INCR": "IINCR",
    "DECR": "IDECR",
    "ADD": "IADD",
    "SUB": "ISUB",
    "MULT": "IMULT",
    "DIV": "IDIV",
    "MOD": "IMOD",
    "CLT": "ICLT",
    "CLE": "ICLE",
    "CEQ": "ICEQ",
    "CNE": "ICNE",
    "CGE": "ICGE",
    "CGT": "ICGT",
}


@dataclass
class StructureIssue:
    code: str
    message: str
    line: int
    is_fatal: bool


@dataclass
class StructureCheckResult:
    warnings: list[StructureIssue] = field(default_factory=list)
    errors: list[StructureIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _validate_identifier(tok: Token, what: str) -> None:
    if not _IDENT_RE.match(tok.value):
        raise ParserError(tok.line_number, f"invalid {what} '{tok.value}'", tok.column)


def _validate_symbol_name(tok: Token, what: str) -> None:
    _validate_identifier(tok, what)
    # Prevent variables/blocks from shadowing instruction mnemonics.
    symbol = tok.value.upper()
    if (
        symbol in NO_OPERAND_MNEMONICS
        or symbol in BRANCH_MNEMONICS
        or symbol in IMMEDIATE_MNEMONICS
        or tok.token_type == "MNEMONIC"
    ):
        raise ParserError(tok.line_number, f"{what} '{tok.value}' cannot be an instruction name", tok.column)
    if tok.value.startswith("."):
        raise ParserError(tok.line_number, f"{what} '{tok.value}' cannot be a directive name", tok.column)


def parse_indexed_symbol(value: str) -> tuple[str, str] | None:
    match = _INDEXED_IDENT_RE.match(value.upper())
    if match is None:
        return None
    return match.group(1), match.group(2)


def parse_literal_indexed_symbol(value: str) -> tuple[str, int] | None:
    indexed = parse_indexed_symbol(value)
    if indexed is None or not indexed[1].isdigit():
        return None
    return indexed[0], int(indexed[1])


def _validate_data_target(tok: Token, what: str) -> None:
    indexed = parse_literal_indexed_symbol(tok.value)
    if indexed is not None:
        base_name = indexed[0]
        _validate_identifier(Token(tok.token_type, base_name, tok.line_number, tok.column), what)
        if base_name in NO_OPERAND_MNEMONICS or base_name in BRANCH_MNEMONICS or base_name in IMMEDIATE_MNEMONICS:
            raise ParserError(tok.line_number, f"{what} '{tok.value}' cannot be an instruction name", tok.column)
        return
    _validate_symbol_name(tok, what)


def _normalize_operands(tokens: list[Token]) -> list[str]:
    return [tok.value for tok in tokens]


def _parse_directive_statement(line_number: int, label: str | None, tokens: list[Token]) -> Statement:
    mnemonic_tok = tokens[0]
    mnemonic = mnemonic_tok.value.upper()
    operands = tokens[1:]

    if mnemonic not in _DIRECTIVES:
        raise ParserError(line_number, f"unknown directive '{mnemonic}'", mnemonic_tok.column)

    if mnemonic in {".BEGIN", ".END"} and operands:
        raise ParserError(
            line_number,
            f"directive {mnemonic} does not take operands",
            operands[0].column,
        )

    if mnemonic == ".ALLOC":
        if len(operands) != 1:
            col = operands[0].column if operands else mnemonic_tok.column
            raise ParserError(line_number, ".ALLOC requires exactly one numeric operand", col)
        if not operands[0].value.isdigit():
            raise ParserError(line_number, ".ALLOC operand must be numeric", operands[0].column)

    if mnemonic == ".DATA":
        if len(operands) < 1:
            raise ParserError(line_number, ".DATA requires at least a variable name", mnemonic_tok.column)
        _validate_data_target(operands[0], "variable name")
        # Accepted forms:
        #   .DATA X
        #   .DATA X = 5
        #   .DATA X =5
        if len(operands) == 1:
            pass
        elif len(operands) == 3 and operands[1].value == "=" and operands[2].value.isdigit():
            pass
        elif len(operands) == 2 and operands[1].value.startswith("=") and operands[1].value[1:].isdigit():
            pass
        else:
            raise ParserError(
                line_number,
                ".DATA expected '.DATA <name> [= <number>]'",
                operands[1].column if len(operands) > 1 else operands[0].column,
            )

    if mnemonic == ".BLOCK":
        if len(operands) < 2:
            col = operands[0].column if operands else mnemonic_tok.column
            raise ParserError(line_number, ".BLOCK expected '.BLOCK <name> <size>' or '.BLOCK <name> =v1,=v2,...'", col)
        _validate_symbol_name(operands[0], "block name")

        # Empty block form: .BLOCK <name> <size>
        if operands[1].value.isdigit():
            if int(operands[1].value) <= 0:
                raise ParserError(line_number, ".BLOCK size must be greater than zero", operands[1].column)
            if len(operands) > 2:
                raise ParserError(
                    line_number,
                    ".BLOCK with explicit values must use '.BLOCK <name> =v1,=v2,...'",
                    operands[2].column,
                )
        else:
            # Initialized form: .BLOCK <name> =v1,=v2,...
            _validate_block_initializer(line_number, operands[1:])

    return Statement(
        line_number=line_number,
        label=label,
        kind="DIRECTIVE",
        mnemonic=mnemonic,
        operands=_normalize_operands(operands),
    )


def _parse_instruction_statement(line_number: int, label: str | None, tokens: list[Token]) -> Statement:
    mnemonic_tok = tokens[0]
    if mnemonic_tok.token_type != "MNEMONIC":
        raise ParserError(line_number, f"expected mnemonic, found '{mnemonic_tok.value}'", mnemonic_tok.column)

    operands = tokens[1:]
    # Grammar in design doc: MNEMONIC [operand]
    if len(operands) > 1:
        raise ParserError(
            line_number,
            f"instruction '{mnemonic_tok.value}' accepts at most one operand",
            operands[1].column,
        )

    return Statement(
        line_number=line_number,
        label=label,
        kind="INSTRUCTION",
        mnemonic=mnemonic_tok.value.upper(),
        operands=_normalize_operands(operands),
    )


def _validate_block_initializer(line_number: int, init_tokens: list[Token]) -> None:
    """
    Accept:
      =6,=5,=4
    """
    if not init_tokens:
        raise ParserError(line_number, ".BLOCK initializer requires at least one value")

    values: list[str] = []
    expect_value = True

    for idx, tok in enumerate(init_tokens):
        if expect_value:
            if tok.token_type != "IMMEDIATE":
                raise ParserError(line_number, ".BLOCK initializer values must be in '=N' form", tok.column)
            if len(tok.value) == 1 or not tok.value[1:].isdigit():
                raise ParserError(line_number, ".BLOCK initializer values must be numeric", tok.column)
            values.append(tok.value[1:])
            expect_value = False
            continue

        if tok.token_type != "COMMA":
            raise ParserError(line_number, "Expected ',' between .BLOCK initializer values", tok.column)
        if idx == len(init_tokens) - 1:
            raise ParserError(line_number, ".BLOCK initializer cannot end with ','", tok.column)
        expect_value = True

    if expect_value:
        raise ParserError(line_number, ".BLOCK initializer cannot end with ','", init_tokens[-1].column)

    if not values:
        raise ParserError(line_number, ".BLOCK initializer requires at least one value", init_tokens[0].column)


def parse_tokens(tokens: list[Token], total_lines: int | None = None) -> list[Statement]:
    statements, errors = parse_tokens_collect(tokens, total_lines=total_lines)
    if errors:
        raise errors[0]
    return statements


def parse_tokens_collect(
    tokens: list[Token],
    total_lines: int | None = None,
) -> tuple[list[Statement], list[ParserError]]:
    by_line: dict[int, list[Token]] = defaultdict(list)
    max_line = 0
    for tok in tokens:
        by_line[tok.line_number].append(tok)
        if tok.line_number > max_line:
            max_line = tok.line_number

    if total_lines is None:
        total_lines = max_line

    statements: list[Statement] = []
    errors: list[ParserError] = []

    for line_number in range(1, total_lines + 1):
        line_tokens = by_line.get(line_number, [])
        code_tokens = [t for t in line_tokens if t.token_type != "COMMENT"]

        if not code_tokens:
            statements.append(Statement(line_number, None, "BLANK", None, []))
            continue

        label: str | None = None
        idx = 0
        if code_tokens[0].token_type == "LABEL_DEF":
            _validate_symbol_name(code_tokens[0], "label name")
            label = code_tokens[0].value
            idx = 1

        if idx >= len(code_tokens):
            # Valid label-only line, used by Pass 1 label scan.
            statements.append(Statement(line_number, label, "BLANK", None, []))
            continue

        body = code_tokens[idx:]
        head = body[0]

        try:
            # Legacy compatibility: allow "name .DATA ..." and "name .BLOCK ..."
            # in addition to ".DATA name ..." / ".BLOCK name ..."
            if (
                len(body) >= 2
                and body[0].token_type in {"OPERAND", "MNEMONIC"}
                and body[1].token_type == "DIRECTIVE"
                and body[1].value in {".DATA", ".BLOCK"}
            ):
                reordered = [body[1], body[0], *body[2:]]
                statements.append(_parse_directive_statement(line_number, label, reordered))
            elif head.token_type == "DIRECTIVE":
                statements.append(_parse_directive_statement(line_number, label, body))
            else:
                statements.append(_parse_instruction_statement(line_number, label, body))
        except ParserError as exc:
            errors.append(exc)
            statements.append(Statement(line_number, None, "BLANK", None, []))

    return statements, errors


def _all_lines(statements: list[Statement], mnemonic: str) -> list[int]:
    return [st.line_number for st in statements if st.kind == "DIRECTIVE" and st.mnemonic == mnemonic]


def check_program_structure(statements: list[Statement]) -> StructureCheckResult:
    """
    Validate cross-line directive ordering rules from the design document.
    """
    result = StructureCheckResult()

    alloc_lines = _all_lines(statements, ".ALLOC")
    data_lines = _all_lines(statements, ".DATA")
    block_lines = _all_lines(statements, ".BLOCK")
    begin_lines = _all_lines(statements, ".BEGIN")
    end_lines = _all_lines(statements, ".END")

    begin_line = begin_lines[0] if begin_lines else None
    end_line = end_lines[-1] if end_lines else None
    alloc_line = alloc_lines[0] if alloc_lines else None

    if begin_line is None:
        result.errors.append(
            StructureIssue(
                code="E002",
                message="No .BEGIN directive found. Every Halix program must have a .BEGIN directive.",
                line=0,
                is_fatal=True,
            )
        )

    if end_line is None:
        result.errors.append(
            StructureIssue(
                code="E003",
                message="No .END directive found. Every Halix program must have a .END directive.",
                line=0,
                is_fatal=True,
            )
        )

    if begin_line is None or end_line is None:
        return result

    if begin_line >= end_line:
        result.errors.append(
            StructureIssue(
                code="E004",
                message=f".BEGIN (line {begin_line}) must precede .END (line {end_line}).",
                line=begin_line,
                is_fatal=True,
            )
        )

    for dname in (".ALLOC", ".DATA", ".BLOCK", ".BEGIN"):
        for ln in _all_lines(statements, dname):
            if ln > end_line:
                result.errors.append(
                    StructureIssue(
                        code="E004",
                        message=(
                            f"{dname} at line {ln} appears after .END (line {end_line}). "
                            ".END must be the last structural directive."
                        ),
                        line=ln,
                        is_fatal=True,
                    )
                )

    for st in statements:
        if st.line_number <= end_line:
            continue
        if st.kind == "BLANK":
            continue
        result.errors.append(
            StructureIssue(
                code="E004",
                message=(
                    f"Statement at line {st.line_number} appears after .END (line {end_line}). "
                    ".END must terminate the program."
                ),
                line=st.line_number,
                is_fatal=True,
            )
        )

    executable_before_end = [
        st for st in statements
        if st.line_number < end_line and st.kind == "INSTRUCTION"
    ]
    if executable_before_end:
        last_instruction = executable_before_end[-1]
        if last_instruction.mnemonic != "HALT":
            result.errors.append(
                StructureIssue(
                    code="E004",
                    message=(
                        f"Last instruction before .END must be HALT, found "
                        f"'{last_instruction.mnemonic}' at line {last_instruction.line_number}."
                    ),
                    line=last_instruction.line_number,
                    is_fatal=True,
                )
            )

    if alloc_line is not None:
        if data_lines and alloc_line > data_lines[0]:
            result.errors.append(
                StructureIssue(
                    code="E004",
                    message=f".ALLOC (line {alloc_line}) must appear before the first .DATA (line {data_lines[0]}).",
                    line=alloc_line,
                    is_fatal=True,
                )
            )
        if alloc_line > begin_line:
            result.errors.append(
                StructureIssue(
                    code="E004",
                    message=f".ALLOC (line {alloc_line}) must appear before .BEGIN (line {begin_line}).",
                    line=alloc_line,
                    is_fatal=True,
                )
            )

    for ln in data_lines:
        if ln > begin_line:
            result.errors.append(
                StructureIssue(
                    code="E004",
                    message=(
                        f".DATA at line {ln} appears after .BEGIN (line {begin_line}). "
                        "All .DATA declarations must precede .BEGIN."
                    ),
                    line=ln,
                    is_fatal=True,
                )
            )

    for ln in block_lines:
        if ln > begin_line:
            result.errors.append(
                StructureIssue(
                    code="E004",
                    message=(
                        f".BLOCK at line {ln} appears after .BEGIN (line {begin_line}). "
                        ".BLOCK declarations must precede .BEGIN."
                    ),
                    line=ln,
                    is_fatal=True,
                )
            )

    if len(begin_lines) > 1:
        result.warnings.append(
            StructureIssue(
                code="W002",
                message=(
                    f"Multiple .BEGIN directives at lines {begin_lines}. "
                    f"First occurrence (line {begin_line}) used."
                ),
                line=begin_line,
                is_fatal=False,
            )
        )

    if len(end_lines) > 1:
        result.warnings.append(
            StructureIssue(
                code="W003",
                message=(
                    f"Multiple .END directives at lines {end_lines}. "
                    f"Last occurrence (line {end_line}) used."
                ),
                line=end_line,
                is_fatal=False,
            )
        )

    if len(alloc_lines) > 1:
        result.errors.append(
            StructureIssue(
                code="E004",
                message=(
                    f"Multiple .ALLOC directives at lines {alloc_lines}. "
                    "Only one .ALLOC directive is allowed."
                ),
                line=alloc_lines[1],
                is_fatal=True,
            )
        )

    # Operand-group validation is only meaningful in executable region.
    for st in statements:
        if st.kind != "INSTRUCTION" or st.mnemonic is None:
            continue
        if st.line_number <= begin_line or st.line_number >= end_line:
            continue

        mnemonic = st.mnemonic.upper()
        operands = st.operands

        if mnemonic in NO_OPERAND_MNEMONICS:
            if operands:
                result.errors.append(
                    StructureIssue(
                        code="E024",
                        message=f"Instruction '{mnemonic}' takes no operand.",
                        line=st.line_number,
                        is_fatal=True,
                    )
                )
            continue

        if mnemonic in BRANCH_MNEMONICS:
            if len(operands) != 1:
                result.errors.append(
                    StructureIssue(
                        code="E025",
                        message=f"Instruction '{mnemonic}' requires exactly one label operand.",
                        line=st.line_number,
                        is_fatal=True,
                    )
                )
                continue
            if not _IDENT_RE.match(operands[0]):
                result.errors.append(
                    StructureIssue(
                        code="E025",
                        message=f"Instruction '{mnemonic}' operand must be a label identifier.",
                        line=st.line_number,
                        is_fatal=True,
                    )
                )
            continue

        if mnemonic in IMMEDIATE_MNEMONICS:
            if len(operands) != 1:
                result.errors.append(
                    StructureIssue(
                        code="E022",
                        message=f"Immediate instruction '{mnemonic}' requires operand in '=N' form.",
                        line=st.line_number,
                        is_fatal=True,
                    )
                )
                continue
            op = operands[0]
            if not op.startswith("="):
                result.errors.append(
                    StructureIssue(
                        code="E022",
                        message=f"Immediate instruction '{mnemonic}' missing '=' prefix.",
                        line=st.line_number,
                        is_fatal=True,
                    )
                )
                continue
            if not op[1:].isdigit():
                result.errors.append(
                    StructureIssue(
                        code="E023",
                        message=f"Immediate instruction '{mnemonic}' has non-numeric value '{op}'.",
                        line=st.line_number,
                        is_fatal=True,
                    )
                )
            continue

        # Default group: data-address instructions require one variable-like operand.
        if len(operands) != 1:
            result.errors.append(
                StructureIssue(
                    code="E026",
                    message=f"Instruction '{mnemonic}' requires exactly one data operand.",
                    line=st.line_number,
                    is_fatal=True,
                )
            )
            continue
        if parse_indexed_symbol(operands[0]) is None and not _IDENT_RE.match(operands[0]):
            result.errors.append(
                StructureIssue(
                    code="E026",
                    message=f"Instruction '{mnemonic}' data operand must be an identifier or indexed block element.",
                    line=st.line_number,
                    is_fatal=True,
                )
            )

    return result


def lower_dynamic_index_operands(
    statements: list[Statement],
) -> tuple[list[Statement], list[ParserError]]:
    lowered: list[Statement] = []
    errors: list[ParserError] = []
    begin_line: int | None = None
    end_line: int | None = None

    for st in statements:
        if st.kind != "DIRECTIVE":
            continue
        if st.mnemonic == ".BEGIN" and begin_line is None:
            begin_line = st.line_number
        if st.mnemonic == ".END":
            end_line = st.line_number

    for st in statements:
        if (
            st.kind != "INSTRUCTION"
            or st.mnemonic is None
            or begin_line is None
            or end_line is None
            or st.line_number <= begin_line
            or st.line_number >= end_line
            or len(st.operands) != 1
        ):
            lowered.append(st)
            continue

        indexed = parse_indexed_symbol(st.operands[0])
        if indexed is None or indexed[1].isdigit():
            lowered.append(st)
            continue

        base_name, index_name = indexed
        indirect_mnemonic = INDIRECT_MNEMONIC_MAP.get(st.mnemonic.upper())
        if indirect_mnemonic is None:
            errors.append(
                ParserError(
                    st.line_number,
                    f"instruction '{st.mnemonic}' does not support dynamic indexed operand '{st.operands[0]}'",
                    code="E026",
                )
            )
            lowered.append(st)
            continue

        lowered.extend(
            [
                Statement(st.line_number, st.label, "INSTRUCTION", "LOADA", [base_name]),
                Statement(st.line_number, None, "INSTRUCTION", "MOVEB", []),
                Statement(st.line_number, None, "INSTRUCTION", "LOAD", [index_name]),
                Statement(st.line_number, None, "INSTRUCTION", "MOVEA", []),
                Statement(st.line_number, None, "INSTRUCTION", indirect_mnemonic, []),
            ]
        )

    return lowered, errors
