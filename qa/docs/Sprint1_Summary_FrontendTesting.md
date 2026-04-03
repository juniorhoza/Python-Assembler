# HLX Assembler — Sprint 1 Frontend Verification

## Summary

Sprint 1 focused on the **Lexer**, **Parser**, and **Program Structure** validation.
This phase ensures that source code is properly tokenized and follows structural rules
(like mandatory `.BEGIN` and `.END` directives) before binary generation is implemented in Sprint 2.

---

## Verification Method: Sabotage Testing

To confirm the tests were correctly importing the development code from `services/`, we performed the following:

1. **The Sabotage:** Injected `raise Exception` into `services/lexer.py` and `services/parser.py`.
2. **The Result:** Both test suites failed with the expected "SABOTAGE" error, proving the link to the active dev code.
3. **The Validation:** Tests were reverted and re-run, returning to 100% PASS.

---

## Test Coverage

| Area | File | Tests |
|------|------|-------|
| Lexer | `test_hlx_unit.py` | LEX-001 – LEX-012 |
| Parser | `test_hlx_unit.py` | PAR-001 – PAR-012 |
| Program Structure | `test_hlx_unit.py` | STR-001 – STR-012 |
| CLI Arguments | `test_hlx_unit.py` | CLI-001 – CLI-007 |
| Real Student File Patterns | `test_hlx_edge_cases.py` | EDGE-001 – EDGE-015 |
| Structural Edge Cases | `test_hlx_edge_cases.py` | EDGE-016 – EDGE-023 |

> **Final Status: 100% PASS — 66 / 66 Tests**

---

## Section 1: Lexer Tests — `test_hlx_unit.py` (12 tests)

These tests verify that the lexer correctly converts raw source text into typed tokens.
They confirm correct token classification, line number tracking, comment handling,
and error detection for invalid input.

| Test ID | Description | Result |
|---------|-------------|--------|
| LEX-001 | `.ALLOC` directive is classified as a `DIRECTIVE` token, not `MNEMONIC` or `UNKNOWN` | PASS |
| LEX-002 | `LOAD` instruction is classified as a `MNEMONIC` token when the opcode set is provided | PASS |
| LEX-003 | An immediate value like `=3` is classified as an `IMMEDIATE` token, not a plain `NUMBER` | PASS |
| LEX-004 | When `keep_comments=False`, comment text (`# ...`) is stripped and not included in the token list | PASS |
| LEX-005 | When `keep_comments=True`, a `COMMENT` token is emitted so the listing file can reproduce the original source | PASS |
| LEX-006 | An illegal character `@` raises a `LexicalError` with the offending line number | PASS |
| LEX-007 | A blank line produces zero tokens — the lexer does not emit phantom whitespace tokens | PASS |
| LEX-008 | A line that is entirely a comment (`# ...`) produces exactly one `COMMENT` token | PASS |
| LEX-009 | A bare integer operand (e.g. `5`) is classified as a `NUMBER` token, distinct from `IMMEDIATE` | PASS |
| LEX-010 | Every emitted token carries the correct source line number for downstream error reporting | PASS |
| LEX-011 | `tokenize_source()` processes a multi-line string and returns one token list covering all lines | PASS |
| LEX-012 | The `.Block` keyword (mixed case) is recognised and produces a `DIRECTIVE` token | PASS |

---

## Section 2: Parser Tests — `test_hlx_unit.py` (12 tests)

These tests verify that the parser correctly converts token streams into structured `Statement` objects.
They cover all directive types, instruction formats, label parsing, and error detection for malformed input.

| Test ID | Description | Result |
|---------|-------------|--------|
| PAR-001 | `.ALLOC N` is parsed into a `Statement` with `kind=DIRECTIVE`, `mnemonic=.ALLOC`, and operand `N` | PASS |
| PAR-002 | `.BEGIN` is parsed as a `DIRECTIVE` statement with no operands | PASS |
| PAR-003 | `.END` is parsed as a `DIRECTIVE` statement with no operands | PASS |
| PAR-004 | A `.DATA` declaration (e.g. `x .DATA =5`) produces a `DIRECTIVE` statement with variable name and value captured | PASS |
| PAR-005 | A `.BLOCK` directive (e.g. `MYARR .BLOCK 5`) produces a `DIRECTIVE` statement with array name and size | PASS |
| PAR-006 | The `HALT` mnemonic is parsed as an `INSTRUCTION` statement with no operands | PASS |
| PAR-007 | `LOAD x` is parsed as `INSTRUCTION` with `mnemonic=LOAD` and `operands=['X']` | PASS |
| PAR-008 | An unrecognised directive keyword (e.g. `.BADDIR`) raises a `ParserError` with the offending line number | PASS |
| PAR-009 | `.ALLOC` with a non-numeric operand (e.g. `.ALLOC abc`) raises a `ParserError` | PASS |
| PAR-010 | `.BLOCK` with no size operand raises a `ParserError` — the array size is mandatory | PASS |
| PAR-011 | `.BLOCK 0` raises a `ParserError` — a zero-size array is not meaningful | PASS |
| PAR-012 | A labelled instruction (`SKIP: LOAD x`) is parsed with `label='SKIP'` and `mnemonic=LOAD` correctly separated | PASS |

---

## Section 3: Program Structure Tests — `test_hlx_unit.py` (12 tests)

These tests verify that the structural validator enforces the required ordering of sections and directives.
They confirm that missing or misplaced directives produce the correct error codes,
and that recoverable issues produce warnings rather than fatal errors.

| Test ID | Description | Result |
|---------|-------------|--------|
| STR-001 | A well-formed program (`.ALLOC` / `.DATA` / `.BEGIN` / code / `.END`) passes structure validation with zero errors | PASS |
| STR-002 | A source file missing `.BEGIN` is detected and reported as structural error `E002` | PASS |
| STR-003 | A source file missing `.END` is detected and reported as structural error `E003` | PASS |
| STR-004 | `.ALLOC` appearing after a `.DATA` line violates ordering rules and is flagged as an error | PASS |
| STR-005 | A `.DATA` directive placed after `.BEGIN` (inside the code section) is caught and reported as an error | PASS |
| STR-006 | A `.BLOCK` directive placed after `.BEGIN` is caught — data declarations must precede the code section | PASS |
| STR-007 | A second `.ALLOC` directive produces warning `W004` rather than a fatal error; assembly continues | PASS |
| STR-008 | Any directive or instruction found after `.END` is flagged as an error — nothing may follow `.END` | PASS |
| STR-009 | `.BEGIN` appearing before `.END` (the normal order) passes the ordering check with no error | PASS |
| STR-010 | A `.BLOCK` directive placed before `.BEGIN` (in the data section) is valid and produces no errors | PASS |
| STR-011 | `HALT` followed by an operand (e.g. `HALT 5`) is detected and reported as error `E024` | PASS |
| STR-012 | `SETI` with an operand missing the `=` prefix (e.g. `SETI 5`) is detected as error `E022` | PASS |

---

## Section 4: CLI Argument Tests — `test_hlx_unit.py` (7 tests)

These tests verify the command-line interface behaviour.
They confirm correct exit codes for all input scenarios.

| Test ID | Description | Result |
|---------|-------------|--------|
| CLI-001 | Running the assembler with `--help` exits with code `0` (success) | PASS |
| CLI-002 | The `--help` output contains at minimum the word "usage", confirming usage information is printed | PASS |
| CLI-003 | Invoking the assembler with no arguments exits with code `1` — missing input error | PASS |
| CLI-004 | Passing a file with the wrong extension (e.g. `source.txt`) exits with code `2` — wrong file type | PASS |
| CLI-005 | Passing a `.hal` filename that does not exist on disk exits with code `3` — file not found | PASS |
| CLI-006 | A valid, well-formed `.hal` file assembles without error and exits with code `0` | PASS |
| CLI-007 | A `.hal` file missing the `.END` directive exits with a non-zero code, confirming structural errors propagate to CLI | PASS |

---

## Section 5: Edge Case Tests — `test_hlx_edge_cases.py` (23 tests)

Edge case tests were derived from real student submissions and structural boundary conditions.
These tests ensure the assembler handles real-world formatting variations correctly.

### Section 5a: Real Student File Patterns (EDGE-001 – EDGE-015)

Based on patterns observed in actual student `.hal` files (mcnairA799, millerI558, crawfordJ558,
starksL369, mooreA953, wagnerO393, bahidikaD374, add2or3, countBy5, 3powers).

| Test ID | Description | Result |
|---------|-------------|--------|
| EDGE-001 | `.ALLOC` preceded by a tab character (mcnairA799, millerI558) is tokenized correctly | PASS |
| EDGE-002 | A duplicate variable name is accepted at parse time — duplicate detection is a Pass 1 scope concern | PASS |
| EDGE-003 | Labels named `IF`, `ELSE`, `ENDIF` (add2or3 pattern) are parsed as valid label identifiers | PASS |
| EDGE-004 | Two `HALT` instructions before `.END` (crawfordJ558 pattern) are both parsed without error | PASS |
| EDGE-005 | A `.DATA` value missing the `=` prefix (e.g. `x .DATA 5`, starksL369 pattern) raises a `ParserError` | PASS |
| EDGE-006 | `.DATA=0` with no whitespace between directive and value (starksL369 pattern) raises a `LexicalError` | PASS |
| EDGE-007 | `ALLOC. 3` (dot placed after the word, mooreA953 pattern) raises a `LexicalError` | PASS |
| EDGE-008 | Multiple consecutive blank lines between sections are skipped cleanly without errors | PASS |
| EDGE-009 | An inline comment on an instruction line is stripped; only the instruction is parsed | PASS |
| EDGE-010 | `.ALLOC N` where `N` is larger than the number of `.DATA` variables is accepted (wagnerO393 pattern) | PASS |
| EDGE-011 | `BRANCH LOOP` (label operand, add2or3 pattern) is parsed with the label captured as the operand | PASS |
| EDGE-012 | `ADDI =5` (immediate mode, countBy5 pattern) is parsed as `INSTRUCTION` with an `IMMEDIATE` operand | PASS |
| EDGE-013 | A file beginning with a large block of comment lines (author header) is parsed correctly | PASS |
| EDGE-014 | `BRF LABEL` (branch-if-false with label operand, bahidikaD374 pattern) is parsed correctly | PASS |
| EDGE-015 | A long instruction sequence (3powers pattern) is parsed in full without hitting any limit | PASS |

### Section 5b: Structural Edge Cases (EDGE-016 – EDGE-023)

These tests probe boundary conditions in the structural validator.

| Test ID | Description | Result |
|---------|-------------|--------|
| EDGE-016 | A minimal valid program containing only `.BEGIN` and `.END` passes structure validation | PASS |
| EDGE-017 | `.ALLOC` appearing after `.BEGIN` raises an error — data declarations must precede the code section | PASS |
| EDGE-018 | A second `.BEGIN` produces warning `W002` rather than a fatal error | PASS |
| EDGE-019 | A second `.END` produces warning `W003` rather than a fatal error | PASS |
| EDGE-020 | `.BLOCK` with initializer values (e.g. `MYARR .BLOCK 3 =1,2,3`) is parsed correctly | PASS |
| EDGE-021 | `.BLOCK` where the number of initializer values exceeds the declared size raises a `ParserError` | PASS |
| EDGE-022 | `CEQ` instruction with an operand (add2or3 pattern) is parsed correctly | PASS |
| EDGE-023 | `CLE` instruction with an operand (countBy5 pattern) is parsed correctly | PASS |

---

## Sprint 1 Status & Notes

| Item | Status |
|------|--------|
| Frontend unit tests (66/66) | ✅ Complete |
| TC-PAR-003, TC-PAR-005 (SCRUM-17) | ✅ Pass at frontend level — full end-to-end blocked pending backend |
| Golden reference `.hlx`/`.hll` files generated | ✅ Complete |
| TC-DIR / TC-PAR / TC-SYM end-to-end | ⏳ Blocked — awaiting Sprint 2 backend implementation |
| Bug log | ✅ No bugs found — 0 failures across all 66 tests |