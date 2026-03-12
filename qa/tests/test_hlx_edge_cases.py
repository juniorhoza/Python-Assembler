"""
test_hlx_edge_cases.py
-----------------------
Edge case unit tests for the HLX Assembler Sprint 1.
Derived from real student .hal files in the project.

Run from repo root:
    python3 qa/tests/test_hlx_edge_cases.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace("qa/tests", ""))

from services.lexer import tokenize_line, tokenize_source, LexicalError
from services.parser import parse_tokens, check_program_structure, ParserError

from services.lexer import tokenize_line
print(f"DEBUG: Lexer loaded from {tokenize_line.__module__}")
# ─────────────────────────────────────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────────────────────────────────────

PASS = 0
FAIL = 0
results = []

def run(test_id, description, fn):
    global PASS, FAIL
    try:
        fn()
        print(f"  PASS  {test_id}  {description}")
        results.append((test_id, "PASS", description, ""))
        PASS += 1
    except AssertionError as e:
        msg = str(e) if str(e) else "assertion failed"
        print(f"  FAIL  {test_id}  {description}")
        print(f"        Reason: {msg}")
        results.append((test_id, "FAIL", description, msg))
        FAIL += 1
    except Exception as e:
        print(f"  FAIL  {test_id}  {description}")
        print(f"        Exception: {type(e).__name__}: {e}")
        results.append((test_id, "FAIL", description, f"{type(e).__name__}: {e}"))
        FAIL += 1


OPCODES = {
    "LOAD", "STORE", "READ", "WRITE", "HALT", "ADD", "SUB", "MULT", "DIV",
    "JUMP", "JUMPGT", "JUMPEQ", "JUMPLT", "JUMPGE", "JUMPLE", "JUMPNE",
    "NOOP", "CLEAR", "SET", "INCR", "DECR", "RET", "BRANCH", "BRT", "BRF",
    "BSUB", "SETI", "ADDI", "SUBI", "MULTI", "DIVI", "MODI",
    "CEQ", "CLE", "CLT", "CGE", "CGT", "CNE",
}

def make_statements(source: str):
    lines = source.strip().splitlines(keepends=True)
    tokens = tokenize_source(lines, opcode_mnemonics=OPCODES)
    return parse_tokens(tokens, total_lines=len(lines))


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: REAL STUDENT FILE PATTERNS
# Derived from actual .hal files submitted by students
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print(" SECTION 1: REAL STUDENT FILE PATTERNS")
print("="*60)


def test_edge_001():
    """
    Seen in: 3powers-mcnairA799.hal, first-millerI558.hal
    .ALLOC with a tab between directive and number: '.ALLOC\t4'
    Should parse normally.
    """
    stmts = make_statements("\t\t.ALLOC\t4\nnum .DATA\n\t\t.BEGIN\nHALT\n\t\t.END")
    allocs = [s for s in stmts if s.mnemonic == ".ALLOC"]
    assert len(allocs) == 1, "Expected .ALLOC parsed with tab spacing"

run("EDGE-001", ".ALLOC with tab spacing (seen in mcnairA799, millerI558)", test_edge_001)


def test_edge_002():
    """
    Seen in: first-crawfordJ558x.hal
    Duplicate variable name 'a' declared twice with .DATA
    Parser should accept both — duplicate label detection is Pass 1 scope (not Sprint 1)
    """
    stmts = make_statements(
        "\t.ALLOC 6\na .DATA =3\nb .DATA =4\nc .DATA\nd .DATA\na .DATA\n\t\t.BEGIN\nHALT\n.END"
    )
    data_stmts = [s for s in stmts if s.mnemonic == ".DATA"]
    assert len(data_stmts) == 5, f"Expected 5 .DATA statements, got {len(data_stmts)}"

run("EDGE-002", "Duplicate variable name accepted by parser (Pass 1 scope)", test_edge_002)


def test_edge_003():
    """
    Seen in: multiple files (add2or3, countBy5)
    Labels on instructions: 'IF:', 'ELSE:', 'ENDIF:', 'WHILE:', 'ENDWHILE:'
    All should parse as labeled INSTRUCTION statements.
    """
    source = (
        "        .ALLOC 2\n"
        "x .DATA =0\ny .DATA\n"
        "        .BEGIN\n"
        "IF:     LOAD x\n"
        "        BRF ELSE\n"
        "        STORE y\n"
        "ELSE:   WRITE x\n"
        "ENDIF:  HALT\n"
        "        .END\n"
    )
    stmts = make_statements(source)
    labeled = [s for s in stmts if s.label is not None]
    labels = [s.label for s in labeled]
    assert "IF" in labels, f"Expected label IF, got {labels}"
    assert "ELSE" in labels, f"Expected label ELSE, got {labels}"
    assert "ENDIF" in labels, f"Expected label ENDIF, got {labels}"

run("EDGE-003", "Labels IF/ELSE/ENDIF on instructions parsed correctly (add2or3 pattern)", test_edge_003)


def test_edge_004():
    """
    Seen in: countBy5-crawfordJ558.hal, add2or3-crawfordJ558.hal
    Two HALT instructions before .END — both should parse as INSTRUCTION statements
    """
    source = (
        "        .ALLOC 1\n"
        "x .DATA\n"
        "        .BEGIN\n"
        "        LOAD x\n"
        "DONE:   HALT\n"
        "        HALT\n"
        "        .END\n"
    )
    stmts = make_statements(source)
    halts = [s for s in stmts if s.mnemonic == "HALT"]
    assert len(halts) == 2, f"Expected 2 HALT statements, got {len(halts)}"

run("EDGE-004", "Two HALT instructions before .END both parsed (crawfordJ558 pattern)", test_edge_004)


def test_edge_005():
    """
    Seen in: 3powers-starksL369.hal
    .DATA with value 0 using space: 'N .DATA 0'
    Note: the parser expects '.DATA name' or '.DATA name =val' — '0' alone is not valid
    This tests that the parser correctly rejects this malformed syntax
    """
    raised = False
    try:
        make_statements("        .ALLOC 1\nN .DATA 0\n        .BEGIN\nHALT\n        .END")
    except ParserError:
        raised = True
    assert raised, "Expected ParserError for '.DATA N 0' (missing = before value)"

run("EDGE-005", ".DATA with value missing = prefix raises ParserError (starksL369 pattern)", test_edge_005)


def test_edge_006():
    """
    Seen in: add2or3-starksL369.hal
    .DATA with no space before =: 'SUM .DATA=0'
    Lexer sees 'DATA=0' as a single token — should raise LexicalError or ParserError
    """
    raised = False
    try:
        make_statements("        .ALLOC 1\nSUM .DATA=0\n        .BEGIN\nHALT\n        .END")
    except (LexicalError, ParserError):
        raised = True
    assert raised, "Expected error for '.DATA=0' with no space"

run("EDGE-006", ".DATA=0 with no space raises error (starksL369 pattern)", test_edge_006)


def test_edge_007():
    """
    Seen in: countBy5-mooreA953.hal
    'ALLOC. 3' — dot after word instead of before
    Should raise LexicalError (invalid token)
    """
    raised = False
    try:
        tokenize_line("ALLOC. 3", 1, opcode_mnemonics=OPCODES)
    except LexicalError:
        raised = True
    assert raised, "Expected LexicalError for 'ALLOC.' (dot after word)"

run("EDGE-007", "'ALLOC. 3' (dot after word) raises LexicalError (mooreA953 pattern)", test_edge_007)


def test_edge_008():
    """
    Seen in: multiple files
    Many blank lines between sections — should not affect parsing
    """
    source = (
        "\n\n\n        .ALLOC 2\n\n\n"
        "x .DATA =3\n\n\n"
        "y .DATA\n\n\n"
        "        .BEGIN\n\n\n"
        "LOAD x\n\n\n"
        "HALT\n\n\n"
        "        .END\n\n\n"
    )
    stmts = make_statements(source)
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True with many blank lines, got {[e.message for e in result.errors]}"

run("EDGE-008", "Many blank lines between sections parsed correctly", test_edge_008)


def test_edge_009():
    """
    Seen in: multiple files (first-greenD236.hal has inline comments)
    Inline comments on instruction lines: 'READ num  # cin >> num'
    Should parse instruction correctly, comment ignored
    """
    stmts = make_statements(
        "        .ALLOC 1\nnum .DATA\n        .BEGIN\n        READ num  # cin >> num\n        HALT\n        .END"
    )
    reads = [s for s in stmts if s.mnemonic == "READ"]
    assert len(reads) == 1, f"Expected one READ, got {len(reads)}"
    assert reads[0].operands == ["NUM"], f"Expected operand NUM, got {reads[0].operands}"

run("EDGE-009", "Inline comment on instruction line ignored correctly", test_edge_009)


def test_edge_010():
    """
    Seen in: add2or3-crawfordJ558.hal
    .ALLOC size larger than actual .DATA declarations (10 reserved, 7 declared)
    Parser should accept this — it's a semantic check not a syntax check
    """
    source = (
        "    .ALLOC 10\n"
        "sum .DATA\nk .DATA\nc2 .DATA\nc3 .DATA\na .DATA\nb .DATA\nc .DATA\n"
        "    .BEGIN\nHALT\n    .END\n"
    )
    stmts = make_statements(source)
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True when .ALLOC > number of .DATA, got {[e.message for e in result.errors]}"

run("EDGE-010", ".ALLOC size larger than .DATA count accepted (wagnerO393 pattern)", test_edge_010)


def test_edge_011():
    """
    Seen in: add2or3 files
    BRANCH instruction with label operand: 'BRANCH ENDIF'
    Should parse as INSTRUCTION with one operand
    """
    source = (
        "        .ALLOC 1\nx .DATA\n        .BEGIN\n"
        "        LOAD x\n"
        "        BRANCH DONE\n"
        "DONE:   HALT\n"
        "        .END\n"
    )
    stmts = make_statements(source)
    branches = [s for s in stmts if s.mnemonic == "BRANCH"]
    assert len(branches) == 1, f"Expected one BRANCH, got {len(branches)}"
    assert branches[0].operands == ["DONE"], f"Expected operand DONE, got {branches[0].operands}"

run("EDGE-011", "BRANCH with label operand parsed correctly (add2or3 pattern)", test_edge_011)


def test_edge_012():
    """
    Seen in: countBy5 files
    ADDI with immediate value: 'ADDI =5'
    Should parse as INSTRUCTION with immediate operand
    """
    source = (
        "        .ALLOC 1\nk .DATA\n        .BEGIN\n"
        "        LOAD k\n"
        "        ADDI =5\n"
        "        STORE k\n"
        "        HALT\n"
        "        .END\n"
    )
    stmts = make_statements(source)
    addis = [s for s in stmts if s.mnemonic == "ADDI"]
    assert len(addis) == 1, f"Expected one ADDI, got {len(addis)}"
    assert addis[0].operands == ["=5"], f"Expected operand =5, got {addis[0].operands}"

run("EDGE-012", "ADDI =5 immediate instruction parsed correctly (countBy5 pattern)", test_edge_012)


def test_edge_013():
    """
    Seen in: multiple files
    Heavy comment header at top of file (10+ comment lines before .ALLOC)
    Should not affect parsing
    """
    source = (
        "# File name: test.hal\n"
        "# Author: Student\n"
        "# Date: 2025\n"
        "# Purpose: Test\n"
        "# PSEUDO-CODE:\n"
        "#   int x;\n"
        "#   cin >> x;\n"
        "#   cout << x;\n"
        "# ==========\n"
        "\n"
        "        .ALLOC 1\n"
        "x .DATA\n"
        "        .BEGIN\n"
        "READ x\n"
        "WRITE x\n"
        "HALT\n"
        "        .END\n"
    )
    stmts = make_statements(source)
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True with comment header, got {[e.message for e in result.errors]}"

run("EDGE-013", "Heavy comment header before .ALLOC parsed correctly", test_edge_013)


def test_edge_014():
    """
    Seen in: add2or3-bahidikaD374.hal
    BRF instruction with label: 'BRF ELSE'
    Should parse as INSTRUCTION with label operand
    """
    source = (
        "        .ALLOC 2\nx .DATA\ny .DATA\n        .BEGIN\n"
        "        LOAD x\n"
        "        BRF SKIP\n"
        "        STORE y\n"
        "SKIP:   HALT\n"
        "        .END\n"
    )
    stmts = make_statements(source)
    brfs = [s for s in stmts if s.mnemonic == "BRF"]
    assert len(brfs) == 1, f"Expected one BRF, got {len(brfs)}"
    assert brfs[0].operands == ["SKIP"], f"Expected operand SKIP, got {brfs[0].operands}"

run("EDGE-014", "BRF with label operand parsed correctly (bahidikaD374 pattern)", test_edge_014)


def test_edge_015():
    """
    Seen in: 3powers-starksL369.hal
    Multiple operations between .BEGIN and .END (cube computation)
    Long instruction sequence should parse without issues
    """
    source = (
        "        .ALLOC 4\n"
        "N .DATA\nX .DATA\nsquare .DATA\ncube .DATA\n"
        "        .BEGIN\n"
        "        READ N\n"
        "        LOAD N\n"
        "        STORE X\n"
        "        WRITE X\n"
        "        LOAD N\n"
        "        MULT N\n"
        "        STORE square\n"
        "        WRITE square\n"
        "        LOAD square\n"
        "        MULT N\n"
        "        STORE cube\n"
        "        WRITE cube\n"
        "        HALT\n"
        "        .END\n"
    )
    stmts = make_statements(source)
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True for long program, got {[e.message for e in result.errors]}"
    instrs = [s for s in stmts if s.kind == "INSTRUCTION"]
    assert len(instrs) >= 13, f"Expected at least 13 instructions, got {len(instrs)}"

run("EDGE-015", "Long instruction sequence (3powers pattern) parsed correctly", test_edge_015)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: STRUCTURAL EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print(" SECTION 2: STRUCTURAL EDGE CASES")
print("="*60)


def test_edge_016():
    """Only .BEGIN and .END, no data section — minimal valid program"""
    stmts = make_statements("        .BEGIN\nHALT\n        .END")
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True for minimal program, got {[e.message for e in result.errors]}"

run("EDGE-016", "Minimal program with only .BEGIN and .END is valid", test_edge_016)


def test_edge_017():
    """.ALLOC appears after .BEGIN — should error"""
    stmts = make_statements("        .BEGIN\n        .ALLOC 2\nx .DATA\nHALT\n        .END")
    result = check_program_structure(stmts)
    assert not result.ok, "Expected error for .ALLOC after .BEGIN"

run("EDGE-017", ".ALLOC after .BEGIN detected as error", test_edge_017)


def test_edge_018():
    """Multiple .BEGIN — warning W002, not error"""
    stmts = make_statements(
        "        .ALLOC 1\nx .DATA\n        .BEGIN\n        .BEGIN\nHALT\n        .END"
    )
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True for multiple .BEGIN (warning only)"
    warn_codes = [w.code for w in result.warnings]
    assert "W002" in warn_codes, f"Expected W002 warning, got {warn_codes}"

run("EDGE-018", "Multiple .BEGIN produces W002 warning not error", test_edge_018)


def test_edge_019():
    """Multiple .END — warning W003, not error"""
    stmts = make_statements(
        "        .ALLOC 1\nx .DATA\n        .BEGIN\nHALT\n        .END\n        .END"
    )
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True for multiple .END (warning only)"
    warn_codes = [w.code for w in result.warnings]
    assert "W003" in warn_codes, f"Expected W003 warning, got {warn_codes}"

run("EDGE-019", "Multiple .END produces W003 warning not error", test_edge_019)


def test_edge_020():
    """.BLOCK with initializer values — valid"""
    stmts = make_statements(
        "        .ALLOC 5\nARR .Block 3 =1,2,3\n        .BEGIN\nHALT\n        .END"
    )
    blocks = [s for s in stmts if s.mnemonic == ".BLOCK"]
    assert len(blocks) == 1, f"Expected one .BLOCK, got {len(blocks)}"

run("EDGE-020", ".BLOCK with initializer values =1,2,3 parsed correctly", test_edge_020)


def test_edge_021():
    """.BLOCK with more initializer values than size — should error"""
    raised = False
    try:
        make_statements(
            "        .ALLOC 5\nARR .Block 2 =1,2,3\n        .BEGIN\nHALT\n        .END"
        )
    except ParserError:
        raised = True
    assert raised, "Expected ParserError for .BLOCK with too many initializer values"

run("EDGE-021", ".BLOCK with more values than size raises ParserError", test_edge_021)


def test_edge_022():
    """CEQ instruction (compare equal) — seen in add2or3 files"""
    source = (
        "        .ALLOC 2\nk .DATA\nc2 .DATA =2\n        .BEGIN\n"
        "        LOAD k\n"
        "        CEQ c2\n"
        "        HALT\n"
        "        .END\n"
    )
    stmts = make_statements(source)
    ceqs = [s for s in stmts if s.mnemonic == "CEQ"]
    assert len(ceqs) == 1, f"Expected one CEQ, got {len(ceqs)}"

run("EDGE-022", "CEQ instruction with operand parsed correctly (add2or3 pattern)", test_edge_022)


def test_edge_023():
    """CLE instruction (compare less or equal) — seen in countBy5 files"""
    source = (
        "        .ALLOC 2\nk .DATA\nLimit .DATA\n        .BEGIN\n"
        "        LOAD k\n"
        "        CLE Limit\n"
        "        HALT\n"
        "        .END\n"
    )
    stmts = make_statements(source)
    cles = [s for s in stmts if s.mnemonic == "CLE"]
    assert len(cles) == 1, f"Expected one CLE, got {len(cles)}"

run("EDGE-023", "CLE instruction with operand parsed correctly (countBy5 pattern)", test_edge_023)


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print(f" RESULTS:  {PASS} PASSED  |  {FAIL} FAILED  |  {PASS+FAIL} TOTAL")
print("="*60)

failed = [(tid, desc, reason) for tid, status, desc, reason in results if status == "FAIL"]
if failed:
    print("\n FAILED TESTS:")
    for tid, desc, reason in failed:
        print(f"   {tid}: {desc}")
        print(f"          {reason}")

print()
sys.exit(0 if FAIL == 0 else 1)
