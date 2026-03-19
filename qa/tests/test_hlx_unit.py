"""
test_hlx_unit.py
-----------------
Unit tests for the HLX Assembler Sprint 1 deliverables.
Tests: lexer.py, parser.py (parse_tokens + check_program_structure)

Run from repo root:
    python3 qa/tests/test_hlx_unit.py

Each test prints PASS or FAIL with a clear reason.
"""

import sys
import os

# Make sure services/ is importable from repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace("qa/tests", ""))

from services.lexer import tokenize_line, tokenize_source, LexicalError
from services.parser import parse_tokens, check_program_structure, ParserError

# ─────────────────────────────────────────────────────────────────────────────
# Test runner helpers
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


# ─────────────────────────────────────────────────────────────────────────────
# Helper: build statements from raw source lines
# ─────────────────────────────────────────────────────────────────────────────

OPCODES = {
    "LOAD", "STORE", "READ", "WRITE", "HALT", "ADD", "SUB", "MULT", "DIV",
    "JUMP", "JUMPGT", "JUMPEQ", "JUMPLT", "JUMPGE", "JUMPLE", "JUMPNE",
    "NOOP", "CLEAR", "SET", "INCR", "DECR", "HALT", "RET", "BRANCH",
    "BRT", "BRF", "BSUB", "SETI", "ADDI", "SUBI", "MULTI", "DIVI", "MODI",
}

def make_statements(source: str):
    lines = source.strip().splitlines(keepends=True)
    tokens = tokenize_source(lines, opcode_mnemonics=OPCODES)
    return parse_tokens(tokens, total_lines=len(lines))


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: LEXER TESTS
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print(" SECTION 1: LEXER TESTS")
print("="*60)

def test_lex_001():
    """Directive token recognized"""
    tokens = tokenize_line("        .ALLOC 4", 1)
    types = [t.token_type for t in tokens]
    assert "DIRECTIVE" in types, f"Expected DIRECTIVE token, got {types}"

run("LEX-001", "Directive .ALLOC produces DIRECTIVE token", test_lex_001)


def test_lex_002():
    """Mnemonic recognized when opcode set provided"""
    tokens = tokenize_line("LOAD    x", 1, opcode_mnemonics=OPCODES)
    types = [t.token_type for t in tokens]
    assert "MNEMONIC" in types, f"Expected MNEMONIC token, got {types}"

run("LEX-002", "Instruction LOAD produces MNEMONIC token", test_lex_002)


def test_lex_003():
    """Immediate value recognized"""
    tokens = tokenize_line("x .DATA =3", 1, opcode_mnemonics=OPCODES)
    types = [t.token_type for t in tokens]
    assert "IMMEDIATE" in types, f"Expected IMMEDIATE token, got {types}"

run("LEX-003", "Immediate value =3 produces IMMEDIATE token", test_lex_003)


def test_lex_004():
    """Comment stripped from code tokens when keep_comments=False"""
    tokens = tokenize_line("LOAD x # this is a comment", 1,
                           opcode_mnemonics=OPCODES, keep_comments=False)
    types = [t.token_type for t in tokens]
    assert "COMMENT" not in types, f"Comment token should be absent, got {types}"

run("LEX-004", "Comment not included when keep_comments=False", test_lex_004)


def test_lex_005():
    """Comment included when keep_comments=True"""
    tokens = tokenize_line("LOAD x # this is a comment", 1,
                           opcode_mnemonics=OPCODES, keep_comments=True)
    types = [t.token_type for t in tokens]
    assert "COMMENT" in types, f"Expected COMMENT token, got {types}"

run("LEX-005", "Comment included when keep_comments=True", test_lex_005)


def test_lex_006():
    """Invalid character raises LexicalError"""
    raised = False
    try:
        tokenize_line("LOAD @x", 1, opcode_mnemonics=OPCODES)
    except LexicalError:
        raised = True
    assert raised, "Expected LexicalError for invalid character @"

run("LEX-006", "Invalid character @ raises LexicalError", test_lex_006)


def test_lex_007():
    """Blank line produces no tokens"""
    tokens = tokenize_line("   ", 1)
    assert tokens == [], f"Expected empty token list for blank line, got {tokens}"

run("LEX-007", "Blank line produces no tokens", test_lex_007)


def test_lex_008():
    """Comment-only line produces one COMMENT token"""
    tokens = tokenize_line("# just a comment", 1, keep_comments=True)
    assert len(tokens) == 1 and tokens[0].token_type == "COMMENT", \
        f"Expected one COMMENT token, got {tokens}"

run("LEX-008", "Comment-only line produces one COMMENT token", test_lex_008)


def test_lex_009():
    """NUMBER token recognized"""
    tokens = tokenize_line(".ALLOC 4", 1)
    types = [t.token_type for t in tokens]
    assert "NUMBER" in types, f"Expected NUMBER token, got {types}"

run("LEX-009", "Numeric operand produces NUMBER token", test_lex_009)


def test_lex_010():
    """Line number is correctly recorded in tokens"""
    tokens = tokenize_line("HALT", 7, opcode_mnemonics=OPCODES)
    assert tokens[0].line_number == 7, \
        f"Expected line_number=7, got {tokens[0].line_number}"

run("LEX-010", "Token records correct line number", test_lex_010)


def test_lex_011():
    """tokenize_source processes multiple lines"""
    source = "        .ALLOC 2\nx .DATA =5\n        .BEGIN\nHALT\n        .END\n"
    lines = source.splitlines(keepends=True)
    tokens = tokenize_source(lines, opcode_mnemonics=OPCODES)
    assert len(tokens) > 0, "Expected tokens from multi-line source"

run("LEX-011", "tokenize_source handles multiple lines", test_lex_011)


def test_lex_012():
    """.BLOCK directive recognized"""
    tokens = tokenize_line("MYARR .Block 5", 1, opcode_mnemonics=OPCODES)
    types = [t.token_type for t in tokens]
    assert "DIRECTIVE" in types, f"Expected DIRECTIVE token for .Block, got {types}"

run("LEX-012", ".Block directive produces DIRECTIVE token", test_lex_012)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: PARSER TESTS
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print(" SECTION 2: PARSER TESTS")
print("="*60)


def test_par_001():
    """Valid .ALLOC parsed as DIRECTIVE statement"""
    stmts = make_statements("        .ALLOC 4\n        .BEGIN\nHALT\n        .END")
    directives = [s for s in stmts if s.kind == "DIRECTIVE" and s.mnemonic == ".ALLOC"]
    assert len(directives) == 1, f"Expected one .ALLOC statement, got {len(directives)}"

run("PAR-001", "Valid .ALLOC parsed as DIRECTIVE statement", test_par_001)


def test_par_002():
    """Valid .BEGIN parsed as DIRECTIVE statement"""
    stmts = make_statements("        .ALLOC 1\nx .DATA\n        .BEGIN\nHALT\n        .END")
    begins = [s for s in stmts if s.kind == "DIRECTIVE" and s.mnemonic == ".BEGIN"]
    assert len(begins) == 1, f"Expected one .BEGIN statement, got {len(begins)}"

run("PAR-002", "Valid .BEGIN parsed as DIRECTIVE statement", test_par_002)


def test_par_003():
    """Valid .END parsed as DIRECTIVE statement"""
    stmts = make_statements("        .ALLOC 1\nx .DATA\n        .BEGIN\nHALT\n        .END")
    ends = [s for s in stmts if s.kind == "DIRECTIVE" and s.mnemonic == ".END"]
    assert len(ends) == 1, f"Expected one .END statement, got {len(ends)}"

run("PAR-003", "Valid .END parsed as DIRECTIVE statement", test_par_003)


def test_par_004():
    """Valid .DATA parsed as DIRECTIVE statement"""
    stmts = make_statements("        .ALLOC 1\nx .DATA =5\n        .BEGIN\nHALT\n        .END")
    data = [s for s in stmts if s.kind == "DIRECTIVE" and s.mnemonic == ".DATA"]
    assert len(data) == 1, f"Expected one .DATA statement, got {len(data)}"

run("PAR-004", "Valid .DATA parsed as DIRECTIVE statement", test_par_004)


def test_par_005():
    """.BLOCK directive parsed correctly"""
    stmts = make_statements("        .ALLOC 6\nMYARR .Block 5\n        .BEGIN\nHALT\n        .END")
    blocks = [s for s in stmts if s.kind == "DIRECTIVE" and s.mnemonic == ".BLOCK"]
    assert len(blocks) == 1, f"Expected one .BLOCK statement, got {len(blocks)}"

run("PAR-005", ".BLOCK directive parsed as DIRECTIVE statement", test_par_005)


def test_par_006():
    """Instruction HALT parsed as INSTRUCTION statement"""
    stmts = make_statements("        .ALLOC 1\nx .DATA\n        .BEGIN\nHALT\n        .END")
    instrs = [s for s in stmts if s.kind == "INSTRUCTION" and s.mnemonic == "HALT"]
    assert len(instrs) == 1, f"Expected one HALT instruction, got {len(instrs)}"

run("PAR-006", "HALT parsed as INSTRUCTION statement", test_par_006)


def test_par_007():
    """Instruction with operand parsed correctly"""
    stmts = make_statements("        .ALLOC 1\nx .DATA =5\n        .BEGIN\nLOAD x\nHALT\n        .END")
    loads = [s for s in stmts if s.kind == "INSTRUCTION" and s.mnemonic == "LOAD"]
    assert len(loads) == 1, f"Expected one LOAD, got {len(loads)}"
    assert loads[0].operands == ["X"], f"Expected operand X, got {loads[0].operands}"

run("PAR-007", "LOAD x parsed with correct operand", test_par_007)


def test_par_008():
    """Unknown directive raises ParserError"""
    raised = False
    try:
        make_statements("        .ALLOC 1\n        .BADDIR\n        .BEGIN\nHALT\n        .END")
    except ParserError:
        raised = True
    assert raised, "Expected ParserError for unknown directive .BADDIR"

run("PAR-008", "Unknown directive .BADDIR raises ParserError", test_par_008)


def test_par_009():
    """.ALLOC requires numeric operand"""
    raised = False
    try:
        make_statements("        .ALLOC abc\n        .BEGIN\nHALT\n        .END")
    except ParserError:
        raised = True
    assert raised, "Expected ParserError for .ALLOC with non-numeric operand"

run("PAR-009", ".ALLOC with non-numeric operand raises ParserError", test_par_009)


def test_par_010():
    """.BLOCK requires name and size"""
    raised = False
    try:
        make_statements("        .ALLOC 1\n.BLOCK\n        .BEGIN\nHALT\n        .END")
    except ParserError:
        raised = True
    assert raised, "Expected ParserError for .BLOCK with no operands"

run("PAR-010", ".BLOCK with no operands raises ParserError", test_par_010)


def test_par_011():
    """.BLOCK size must be positive"""
    raised = False
    try:
        make_statements("        .ALLOC 1\nARR .Block 0\n        .BEGIN\nHALT\n        .END")
    except ParserError:
        raised = True
    assert raised, "Expected ParserError for .BLOCK size=0"

run("PAR-011", ".BLOCK with size 0 raises ParserError", test_par_011)


def test_par_012():
    """Label on instruction parsed correctly"""
    stmts = make_statements("        .ALLOC 1\nx .DATA\n        .BEGIN\nSKIP: HALT\n        .END")
    labeled = [s for s in stmts if s.label == "SKIP"]
    assert len(labeled) == 1, f"Expected one labeled statement, got {len(labeled)}"

run("PAR-012", "Label SKIP: on instruction parsed correctly", test_par_012)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: STRUCTURE CHECK TESTS (check_program_structure)
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print(" SECTION 3: PROGRAM STRUCTURE TESTS")
print("="*60)


def test_str_001():
    """Valid program structure passes"""
    stmts = make_statements(
        "        .ALLOC 2\nx .DATA =3\ny .DATA\n        .BEGIN\nLOAD x\nSTORE y\nHALT\n        .END"
    )
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True, got errors: {[e.message for e in result.errors]}"

run("STR-001", "Valid program structure passes with no errors", test_str_001)


def test_str_002():
    """Missing .BEGIN detected"""
    stmts = make_statements("        .ALLOC 1\nx .DATA\nHALT\n        .END")
    result = check_program_structure(stmts)
    assert not result.ok, "Expected error for missing .BEGIN"
    codes = [e.code for e in result.errors]
    assert "E002" in codes, f"Expected error code E002, got {codes}"

run("STR-002", "Missing .BEGIN detected with error E002", test_str_002)


def test_str_003():
    """Missing .END detected"""
    stmts = make_statements("        .ALLOC 1\nx .DATA\n        .BEGIN\nHALT")
    result = check_program_structure(stmts)
    assert not result.ok, "Expected error for missing .END"
    codes = [e.code for e in result.errors]
    assert "E003" in codes, f"Expected error code E003, got {codes}"

run("STR-003", "Missing .END detected with error E003", test_str_003)


def test_str_004():
    """.ALLOC after .DATA detected"""
    stmts = make_statements("x .DATA =5\n        .ALLOC 2\ny .DATA\n        .BEGIN\nHALT\n        .END")
    result = check_program_structure(stmts)
    assert not result.ok, "Expected error for .ALLOC appearing after .DATA"

run("STR-004", ".ALLOC after .DATA detected as error", test_str_004)


def test_str_005():
    """.DATA after .BEGIN detected"""
    stmts = make_statements("        .ALLOC 1\n        .BEGIN\nx .DATA =5\nHALT\n        .END")
    result = check_program_structure(stmts)
    assert not result.ok, "Expected error for .DATA after .BEGIN"

run("STR-005", ".DATA after .BEGIN detected as error", test_str_005)


def test_str_006():
    """.BLOCK after .BEGIN detected"""
    stmts = make_statements("        .ALLOC 1\n        .BEGIN\nARR .Block 3\nHALT\n        .END")
    result = check_program_structure(stmts)
    assert not result.ok, "Expected error for .BLOCK after .BEGIN"

run("STR-006", ".BLOCK after .BEGIN detected as error", test_str_006)


def test_str_007():
    """Multiple .ALLOC produces warning W004 not error"""
    stmts = make_statements(
        "        .ALLOC 2\nx .DATA =3\n        .ALLOC 2\ny .DATA\n        .BEGIN\nHALT\n        .END"
    )
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True for multiple .ALLOC (warning only), got errors: {[e.message for e in result.errors]}"
    warn_codes = [w.code for w in result.warnings]
    assert "W004" in warn_codes, f"Expected warning W004, got {warn_codes}"

run("STR-007", "Multiple .ALLOC produces W004 warning not error", test_str_007)


def test_str_008():
    """Directive after .END detected"""
    stmts = make_statements(
        "        .ALLOC 1\nx .DATA\n        .BEGIN\nHALT\n        .END\nx .DATA =5"
    )
    result = check_program_structure(stmts)
    assert not result.ok, "Expected error for .DATA after .END"

run("STR-008", "Directive after .END detected as error", test_str_008)


def test_str_009():
    """.BEGIN before .END passes ordering check"""
    stmts = make_statements("        .ALLOC 1\nx .DATA\n        .BEGIN\nHALT\n        .END")
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True, got errors: {[e.message for e in result.errors]}"

run("STR-009", ".BEGIN before .END passes ordering check", test_str_009)


def test_str_010():
    """.BLOCK before .BEGIN is valid"""
    stmts = make_statements(
        "        .ALLOC 6\nMYARR .Block 5\nn .DATA =1\n        .BEGIN\nLOAD n\nHALT\n        .END"
    )
    result = check_program_structure(stmts)
    assert result.ok, f"Expected ok=True for .BLOCK before .BEGIN, got {[e.message for e in result.errors]}"

run("STR-010", ".BLOCK before .BEGIN is valid — no errors", test_str_010)


def test_str_011():
    """No operand instruction with operand detected"""
    stmts = make_statements("        .ALLOC 1\nx .DATA\n        .BEGIN\nHALT x\n        .END")
    result = check_program_structure(stmts)
    assert not result.ok, "Expected error for HALT with operand"
    codes = [e.code for e in result.errors]
    assert "E024" in codes, f"Expected E024, got {codes}"

run("STR-011", "HALT with operand detected as error E024", test_str_011)


def test_str_012():
    """Immediate instruction missing = prefix detected"""
    stmts = make_statements("        .ALLOC 1\nx .DATA\n        .BEGIN\nSETI 5\nHALT\n        .END")
    result = check_program_structure(stmts)
    assert not result.ok, "Expected error for SETI without = prefix"
    codes = [e.code for e in result.errors]
    assert "E022" in codes, f"Expected E022, got {codes}"

run("STR-012", "SETI without = prefix detected as error E022", test_str_012)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: CLI ARGUMENT TESTS
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print(" SECTION 4: CLI ARGUMENT TESTS")
print("="*60)

import subprocess

def run_cli(args):
    """Run HASM_CLI.py with given args, return (exit_code, stdout+stderr)"""
    result = subprocess.run(
        ["python3", "HASM_CLI.py"] + args,
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)).replace("/qa/tests", "")
    )
    return result.returncode, result.stdout + result.stderr


def test_cli_001():
    """--help returns exit code 0"""
    code, _ = run_cli(["--help"])
    assert code == 0, f"Expected exit code 0 for --help, got {code}"

run("CLI-001", "--help flag returns exit code 0", test_cli_001)


def test_cli_002():
    """--help output contains usage info"""
    code, out = run_cli(["--help"])
    assert "usage" in out.lower() or "source_file" in out.lower(), \
        f"Expected usage info in --help output"

run("CLI-002", "--help output contains usage information", test_cli_002)


def test_cli_003():
    """No arguments returns exit code 1"""
    code, _ = run_cli([])
    assert code == 1, f"Expected exit code 1 for no args, got {code}"

run("CLI-003", "No arguments returns exit code 1", test_cli_003)


def test_cli_004():
    """Wrong extension returns exit code 2"""
    code, _ = run_cli(["somefile.txt"])
    assert code == 2, f"Expected exit code 2 for wrong extension, got {code}"

run("CLI-004", "Wrong file extension (.txt) returns exit code 2", test_cli_004)


def test_cli_005():
    """Non-existent file returns exit code 3"""
    code, _ = run_cli(["doesnotexist.hal"])
    assert code == 3, f"Expected exit code 3 for missing file, got {code}"

run("CLI-005", "Non-existent .hal file returns exit code 3", test_cli_005)


def test_cli_006():
    """Valid file returns exit code 0"""
    code, _ = run_cli(["qa/tests/inputs/TC-PAR-001.hal"])
    assert code == 0, f"Expected exit code 0 for valid file, got {code}"

run("CLI-006", "Valid .hal file returns exit code 0", test_cli_006)


def test_cli_007():
    """Invalid .hal file with structural error returns non-zero exit code"""
    code, _ = run_cli(["qa/tests/inputs/TC-DIR-003b.hal"])
    assert code != 0, f"Expected non-zero exit code for file missing .END, got {code}"

run("CLI-007", "File missing .END returns non-zero exit code", test_cli_007)


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print(f" RESULTS:  {PASS} PASSED  |  {FAIL} FAILED  |  {PASS+FAIL} TOTAL")
print("="*60)

if results:
    failed = [(tid, desc, reason) for tid, status, desc, reason in results if status == "FAIL"]
    if failed:
        print("\n FAILED TESTS:")
        for tid, desc, reason in failed:
            print(f"   {tid}: {desc}")
            print(f"          {reason}")

print()
sys.exit(0 if FAIL == 0 else 1)
