"""
hasm_directive_checker.py
--------------------------
Validates the structural ordering and constraints of Halix assembler
directives before pass-1 or pass-2 processing begins.

Confirmed legacy rules (source: HASM_v25 csh script):
  - .BEGIN is required (legacy exit 7)
  - .END   is required (legacy exit 8)
  - .ALLOC is optional; if present, must appear before .DATA and .BEGIN
  - .DATA  is optional; all .DATA lines must appear before .BEGIN
  - .BEGIN must precede .END
  - .END   must be the last structural directive in the file

Client-confirmed enhancement:
  - .BLOCK is now a supported directive (confirmed by client feedback)
  - .BLOCK must appear before .BEGIN (in the data declaration region)

Legacy behavior on duplicates:
  - Multiple .BEGIN: first occurrence is used (warning issued)
  - Multiple .END:   last  occurrence is used (warning issued)
  - Multiple .ALLOC: first occurrence used (warning issued)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DirectiveLocation:
    name: str
    line_numbers: list[int] = field(default_factory=list)

    @property
    def first(self) -> Optional[int]:
        return self.line_numbers[0] if self.line_numbers else None

    @property
    def last(self) -> Optional[int]:
        return self.line_numbers[-1] if self.line_numbers else None

    @property
    def found(self) -> bool:
        return bool(self.line_numbers)

    @property
    def count(self) -> int:
        return len(self.line_numbers)


@dataclass
class DirectiveCheckResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    alloc_line:  Optional[int] = None
    begin_line:  Optional[int] = None
    end_line:    Optional[int] = None
    data_lines:  list[int] = field(default_factory=list)
    block_lines: list[int] = field(default_factory=list)   # client-confirmed

    @property
    def ok(self) -> bool:
        return not self.errors


# All recognized structural directives including client-confirmed .BLOCK
DIRECTIVE_TOKENS = {".ALLOC", ".DATA", ".BLOCK", ".BEGIN", ".END"}


def _scan_directives(source_lines: list[str]) -> dict[str, DirectiveLocation]:
    locations = {d: DirectiveLocation(name=d) for d in DIRECTIVE_TOKENS}
    for lineno, raw in enumerate(source_lines, start=1):
        text = raw.split("#")[0].strip()
        if not text:
            continue
        first_token = text.split()[0].upper()
        if first_token in locations:
            locations[first_token].line_numbers.append(lineno)
    return locations


def check_directives(source_lines: list[str]) -> DirectiveCheckResult:
    result = DirectiveCheckResult()
    locs = _scan_directives(source_lines)

    alloc = locs[".ALLOC"]
    data  = locs[".DATA"]
    block = locs[".BLOCK"]
    begin = locs[".BEGIN"]
    end   = locs[".END"]

    # R1: .BEGIN required
    if not begin.found:
        result.errors.append(
            "FATAL: No .BEGIN directive found. "
            "Every Halix program must have a .BEGIN directive."
        )

    # R2: .END required
    if not end.found:
        result.errors.append(
            "FATAL: No .END directive found. "
            "Every Halix program must have a .END directive."
        )

    if not begin.found or not end.found:
        return result

    canonical_begin = begin.first
    canonical_end   = end.last

    result.begin_line = canonical_begin
    result.end_line   = canonical_end

    # R3: .BEGIN must precede .END
    if canonical_begin >= canonical_end:
        result.errors.append(
            f"FATAL: .BEGIN (line {canonical_begin}) must precede "
            f".END (line {canonical_end})."
        )

    # R4: Nothing structural after last .END
    for d in [".ALLOC", ".DATA", ".BLOCK", ".BEGIN"]:
        for ln in locs[d].line_numbers:
            if ln > canonical_end:
                result.errors.append(
                    f"FATAL: {d} at line {ln} appears after "
                    f".END (line {canonical_end}). "
                    f".END must be the last structural directive."
                )

    # R5: .ALLOC must appear before .DATA and .BEGIN
    if alloc.found:
        result.alloc_line = alloc.first
        if data.found and alloc.first > data.first:
            result.errors.append(
                f"FATAL: .ALLOC (line {alloc.first}) must appear before "
                f"the first .DATA (line {data.first})."
            )
        if alloc.first > canonical_begin:
            result.errors.append(
                f"FATAL: .ALLOC (line {alloc.first}) must appear before "
                f".BEGIN (line {canonical_begin})."
            )

    # R6: All .DATA lines must appear before .BEGIN
    for ln in data.line_numbers:
        if ln > canonical_begin:
            result.errors.append(
                f"FATAL: .DATA at line {ln} appears after "
                f".BEGIN (line {canonical_begin}). "
                f"All .DATA declarations must precede .BEGIN."
            )
    result.data_lines = [ln for ln in data.line_numbers if ln <= canonical_begin]

    # R7: .BLOCK lines must appear before .BEGIN (client-confirmed enhancement)
    for ln in block.line_numbers:
        if ln > canonical_begin:
            result.errors.append(
                f"FATAL: .BLOCK at line {ln} appears after "
                f".BEGIN (line {canonical_begin}). "
                f".BLOCK declarations must precede .BEGIN."
            )
    result.block_lines = [ln for ln in block.line_numbers if ln <= canonical_begin]

    # W1: Multiple .BEGIN
    if begin.count > 1:
        result.warnings.append(
            f"WARNING: Multiple .BEGIN directives at lines {begin.line_numbers}. "
            f"First occurrence (line {canonical_begin}) used."
        )

    # W2: Multiple .END
    if end.count > 1:
        result.warnings.append(
            f"WARNING: Multiple .END directives at lines {end.line_numbers}. "
            f"Last occurrence (line {canonical_end}) used."
        )

    # W3: Multiple .ALLOC
    if alloc.count > 1:
        result.warnings.append(
            f"WARNING: Multiple .ALLOC directives at lines {alloc.line_numbers}. "
            f"First occurrence (line {alloc.first}) used."
        )

    return result


def report_results(result: DirectiveCheckResult, source_file: str = "") -> None:
    label = f" [{source_file}]" if source_file else ""
    for w in result.warnings:
        print(w)
    for e in result.errors:
        print(e)
    if result.ok:
        print(f"Directive structure OK{label}.")
    else:
        print(f"\n***** FATAL ERROR: Directive structure invalid{label}. Assembly halted.")