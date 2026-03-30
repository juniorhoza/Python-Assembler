"""
lexer.py
--------
Tokenizes Halix source lines into a flat list of Token objects.
"""

from dataclasses import dataclass
import re
from typing import Iterable, Optional


@dataclass
class Token:
    token_type: str
    value: str
    line_number: int
    column: int


class LexicalError(Exception):
    def __init__(self, line: int, column: int, token: str, code: str = "E005"):
        self.code = code
        self.line = line
        self.column = column
        self.token = token
        super().__init__(str(self))

    def __str__(self) -> str:
        return f"invalid token '{self.token}' at column {self.column}"


_DIRECTIVE_RE = re.compile(r"^\.[A-Za-z][A-Za-z0-9_]*$")
_LABEL_DEF_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*:$")
_IMMEDIATE_RE = re.compile(r"^=\S+$")
_NUMBER_RE = re.compile(r"^\d+$")
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INDEXED_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\[\d+\]$")


def _invalid_char(raw: str) -> Optional[str]:
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_:.=,[]")
    for ch in raw:
        if ch not in allowed:
            return ch
    return None


def _classify_identifier(
    raw: str,
    index: int,
    prev_type: Optional[str],
    opcode_mnemonics: set[str],
) -> str:
    upper = raw.upper()
    if upper in opcode_mnemonics:
        return "MNEMONIC"
    if index == 0 and prev_type is None:
        return "OPERAND"
    return "OPERAND"


def _split_attached_commas(raw: str, col: int) -> list[tuple[str, int]]:
    """
    Split tokens like '1,2,3' into [('1', c), (',', c+1), ('2', c+2), ...]
    while preserving 1-based columns.
    """
    parts: list[tuple[str, int]] = []
    start = 0
    for idx, ch in enumerate(raw):
        if ch != ",":
            continue
        if start < idx:
            parts.append((raw[start:idx], col + start))
        parts.append((",", col + idx))
        start = idx + 1
    if start < len(raw):
        parts.append((raw[start:], col + start))
    if not parts:
        parts.append((raw, col))
    return parts


def tokenize_line(
    line: str,
    line_number: int,
    opcode_mnemonics: Optional[set[str]] = None,
    keep_comments: bool = True,
) -> list[Token]:
    if opcode_mnemonics is None:
        opcode_mnemonics = set()

    tokens: list[Token] = []

    # Split comment from code, preserving comment token if requested.
    comment_index = line.find("#")
    code_part = line if comment_index < 0 else line[:comment_index]
    comment_token: Optional[Token] = None
    if comment_index >= 0 and keep_comments:
        comment_text = line[comment_index + 1 :].strip()
        comment_token = Token("COMMENT", comment_text, line_number, comment_index + 1)

    if not code_part.strip():
        if comment_token is not None:
            tokens.append(comment_token)
        return tokens

    prev_type: Optional[str] = None
    split_index = 0
    for match in re.finditer(r"\S+", code_part):
        raw = match.group(0)
        col = match.start() + 1

        invalid = _invalid_char(raw)
        if invalid is not None:
            bad_col = col + raw.index(invalid)
            raise LexicalError(line_number, bad_col, invalid)

        for part_raw, part_col in _split_attached_commas(raw, col):
            if part_raw == ",":
                token = Token("COMMA", part_raw, line_number, part_col)
            elif part_raw == "=":
                token = Token("ASSIGN", part_raw, line_number, part_col)
            elif _DIRECTIVE_RE.match(part_raw):
                token = Token("DIRECTIVE", part_raw.upper(), line_number, part_col)
            elif _LABEL_DEF_RE.match(part_raw):
                token = Token("LABEL_DEF", part_raw[:-1].upper(), line_number, part_col)
            elif _IMMEDIATE_RE.match(part_raw):
                token = Token("IMMEDIATE", part_raw, line_number, part_col)
            elif _NUMBER_RE.match(part_raw):
                token = Token("NUMBER", part_raw, line_number, part_col)
            elif _INDEXED_IDENT_RE.match(part_raw):
                token = Token("OPERAND", part_raw.upper(), line_number, part_col)
            elif _IDENT_RE.match(part_raw):
                token_type = _classify_identifier(part_raw, split_index, prev_type, opcode_mnemonics)
                token = Token(token_type, part_raw.upper(), line_number, part_col)
            else:
                raise LexicalError(line_number, part_col, part_raw)

            tokens.append(token)
            prev_type = token.token_type
            split_index += 1

    if comment_token is not None:
        tokens.append(comment_token)
    return tokens


def tokenize_source(
    source_lines: Iterable[str],
    opcode_mnemonics: Optional[set[str]] = None,
    keep_comments: bool = True,
) -> list[Token]:
    tokens, errors = tokenize_source_collect(
        source_lines=source_lines,
        opcode_mnemonics=opcode_mnemonics,
        keep_comments=keep_comments,
    )
    if errors:
        raise errors[0]
    return tokens


def tokenize_source_collect(
    source_lines: Iterable[str],
    opcode_mnemonics: Optional[set[str]] = None,
    keep_comments: bool = True,
) -> tuple[list[Token], list[LexicalError]]:
    if opcode_mnemonics is None:
        opcode_mnemonics = set()

    all_tokens: list[Token] = []
    errors: list[LexicalError] = []
    for line_number, line in enumerate(source_lines, start=1):
        try:
            all_tokens.extend(
                tokenize_line(
                    line=line,
                    line_number=line_number,
                    opcode_mnemonics=opcode_mnemonics,
                    keep_comments=keep_comments,
                )
            )
        except LexicalError as exc:
            errors.append(exc)
    return all_tokens, errors


def tokenize_file(
    source_path: str,
    opcode_mnemonics: Optional[set[str]] = None,
    keep_comments: bool = True,
) -> list[Token]:
    with open(source_path, "r") as f:
        return tokenize_source(f.readlines(), opcode_mnemonics=opcode_mnemonics, keep_comments=keep_comments)
