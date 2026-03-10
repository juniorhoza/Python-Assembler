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
    def __init__(self, line: int, message: str, column: int | None = None):
        self.line = line
        self.message = message
        self.column = column
        super().__init__(str(self))

    def __str__(self) -> str:
        if self.column is None:
            return f"Parser Error at line {self.line}: {self.message}"
        return f"Parser Error at line {self.line}, column {self.column}: {self.message}"


_IDENT_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
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
    if tok.token_type == "MNEMONIC":
        raise ParserError(tok.line_number, f"{what} '{tok.value}' cannot be an instruction name", tok.column)


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
        _validate_symbol_name(operands[0], "variable name")
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
        # Array-style declaration: .BLOCK <name> <size>
        if len(operands) < 2:
            col = operands[0].column if operands else mnemonic_tok.column
            raise ParserError(line_number, ".BLOCK expected '.BLOCK <name> <size> [= v1,v2,...]'", col)
        _validate_symbol_name(operands[0], "block name")
        if not operands[1].value.isdigit():
            raise ParserError(line_number, ".BLOCK size must be numeric", operands[1].column)
        if int(operands[1].value) <= 0:
            raise ParserError(line_number, ".BLOCK size must be greater than zero", operands[1].column)
        if len(operands) > 2:
            _validate_block_initializer(line_number, operands[2:], int(operands[1].value))

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


def _validate_block_initializer(line_number: int, init_tokens: list[Token], block_size: int) -> None:
    """
    Accept:
      = 1,2,3
      =1,2,3
    """
    values: list[str] = []
    idx = 0

    expect_value = True

    if init_tokens[0].token_type == "ASSIGN":
        idx = 1
    elif init_tokens[0].token_type == "IMMEDIATE":
        first = init_tokens[0].value
        if len(first) == 1:
            raise ParserError(line_number, ".BLOCK initializer missing first value after '='", init_tokens[0].column)
        values.append(first[1:])
        idx = 1
        expect_value = False
    else:
        raise ParserError(line_number, ".BLOCK initializer must start with '='", init_tokens[0].column)
    while idx < len(init_tokens):
        tok = init_tokens[idx]
        if expect_value:
            if tok.token_type == "NUMBER":
                values.append(tok.value)
                expect_value = False
            elif tok.token_type == "IMMEDIATE":
                # allow '=7' in list positions for leniency
                if len(tok.value) == 1 or not tok.value[1:].isdigit():
                    raise ParserError(line_number, ".BLOCK initializer values must be numeric", tok.column)
                values.append(tok.value[1:])
                expect_value = False
            else:
                raise ParserError(line_number, ".BLOCK initializer values must be numeric", tok.column)
        else:
            if tok.token_type != "COMMA":
                raise ParserError(line_number, "Expected ',' between .BLOCK initializer values", tok.column)
            expect_value = True
        idx += 1

    if expect_value:
        raise ParserError(line_number, ".BLOCK initializer cannot end with ','", init_tokens[-1].column)

    if len(values) > block_size:
        raise ParserError(
            line_number,
            f".BLOCK initializer has {len(values)} values but block size is {block_size}",
            init_tokens[0].column,
        )


def parse_tokens(tokens: list[Token], total_lines: int | None = None) -> list[Statement]:
    by_line: dict[int, list[Token]] = defaultdict(list)
    max_line = 0
    for tok in tokens:
        by_line[tok.line_number].append(tok)
        if tok.line_number > max_line:
            max_line = tok.line_number

    if total_lines is None:
        total_lines = max_line

    statements: list[Statement] = []

    for line_number in range(1, total_lines + 1):
        line_tokens = by_line.get(line_number, [])
        code_tokens = [t for t in line_tokens if t.token_type != "COMMENT"]

        if not code_tokens:
            statements.append(Statement(line_number, None, "BLANK", None, []))
            continue

        label: str | None = None
        idx = 0
        if code_tokens[0].token_type == "LABEL_DEF":
            label = code_tokens[0].value
            idx = 1

        if idx >= len(code_tokens):
            # Valid label-only line, used by Pass 1 label scan.
            statements.append(Statement(line_number, label, "BLANK", None, []))
            continue

        body = code_tokens[idx:]
        head = body[0]

        if head.token_type == "DIRECTIVE":
            statements.append(_parse_directive_statement(line_number, label, body))
        else:
            statements.append(_parse_instruction_statement(line_number, label, body))

    return statements


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
        result.warnings.append(
            StructureIssue(
                code="W004",
                message=(
                    f"Multiple .ALLOC directives at lines {alloc_lines}. "
                    f"First occurrence (line {alloc_line}) used."
                ),
                line=alloc_line if alloc_line is not None else 0,
                is_fatal=False,
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
        if not _IDENT_RE.match(operands[0]):
            result.errors.append(
                StructureIssue(
                    code="E026",
                    message=f"Instruction '{mnemonic}' data operand must be an identifier.",
                    line=st.line_number,
                    is_fatal=True,
                )
            )

    return result
