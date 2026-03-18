# HLX Assembler

A two-pass assembler for the **Halix computer architecture**, implemented in Python 3.  
Translates Halix assembly language (`.hal`) source files into Halix machine code (`.hlx`) and produces a human-readable listing file (`.hll`).

> Developed as a team software engineering project for **CEN 5075 — Software Systems Engineering**, Florida A&M University.  
> Reference assembler: `HASM_v25.csh` (C-Shell, Prof. Jones).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [File Types](#file-types)
- [Supported Directives](#supported-directives)
- [Installation](#installation)
- [Usage](#usage)
- [Output Files](#output-files)
- [Error Reporting](#error-reporting)
- [Project Structure](#project-structure)
- [Halix Architecture Quick Reference](#halix-architecture-quick-reference)
- [Running the Tests](#running-the-tests)
- [Team](#team)

---

## Overview

The HLX Assembler sits between the assembly-language programmer and the Halix computer (or its simulator). It performs the classic two-pass assembly strategy:

| Pass | What Happens |
|------|-------------|
| **Pass 1** | Scan the source file; build a **data symbol table** (variables → data addresses) and an **instruction label table** (labels → instruction addresses). |
| **Pass 2** | Re-scan all statements; look up every mnemonic in the opcode table, resolve all operands through the symbol tables, and emit 4-digit machine words. |

The assembler validates syntax, mnemonics, directives, operands, and structural constraints at each stage, and reports all errors with source-line references.

---

## Architecture

The Python implementation is organized into **7 independently testable modules**, mirroring the logical structure of the reference C-Shell assembler:

```
main.py          ← CLI entry point; validates .hal extension; starts pipeline
lexer.py         ← Tokenises raw source; strips comments; tracks line numbers
parser.py        ← Converts token stream into structured Statement objects
pass1.py         ← Builds DataTable (variables) and LabelTable (instruction labels)
opcode_table.py  ← Loads mnemonic → 2-digit opcode mapping from halix_v25.opcode
pass2.py         ← Encodes each statement into a 4-digit machine word
output.py        ← Writes .hlx machine code file and .hll listing file
errors.py        ← Centralised error collection; formatted messages to stderr
```

**Pipeline data flow:**

```
prog.hal
  │
  ▼
[Lexer] ──► Token list
  │
  ▼
[Parser] ──► Statement list
  │
  ├──► [Pass 1] ──► DataTable + LabelTable
  │
  ├──► [Opcode Table Loader] ──► OpcodeTable dict
  │
  ├──► [Pass 2 / Encoder] ──► List of 4-digit machine words
  │
  └──► [Output Module] ──► prog.hlx  +  prog.hll
                      ──► [Error Handler] ──► stderr  (on any error)
```

---

## File Types

| Extension | Description |
|-----------|-------------|
| `.hal`    | Halix assembly language source file (input) |
| `.hlx`    | Halix machine code output file |
| `.hll`    | Assembler listing file — relates source lines to generated machine words |

---

## Supported Directives

| Directive | Purpose |
|-----------|---------|
| `.ALLOC N` | Declare data memory size `N`. Must appear first and only once. |
| `.DATA name = value` | Declare a variable with an explicit initial value. |
| `.DATA name` | Declare a variable; default initial value is `9999`. |
| `.BEGIN` | Marks the start of the executable code section. |
| `.END` | Marks the end of the program. Must be the last statement. |
| `.BLOCK` | *(Draft — confirm with client before relying on this)* Allocates a contiguous block of memory. |

> **Note:** Comments begin with `#` and may appear anywhere on a line.

---

## Installation

**Requirements:** Python 3.8 or later. No third-party packages required.

```bash
git clone https://github.com/<your-org>/hlx-assembler.git
cd hlx-assembler
```

Optionally, verify your Python version:

```bash
python3 --version
```

---

## Usage

```bash
python3 main.py <source_file>.hal
```

**Example:**

```bash
python3 main.py programs/first.hal
```

This produces `first.hlx` and `first.hll` in the same directory as the source file.

**Help flag:**

```bash
python3 main.py --help
```

### Source File Structure

Every valid `.hal` file must follow this exact section order:

```
# Optional comment lines

.ALLOC N                    # Declare data memory size

.DATA varname = value       # One or more data declarations
.DATA varname               # (default value 9999)

.BEGIN                      # Start of code section

LABEL:  MNEMONIC operand    # Labelled instruction
        MNEMONIC operand    # Unlabelled instruction
        HALT                # Program must end with HALT

.END                        # End of program
```

---

## Output Files

### `.hlx` Machine Code File

```
<code_size>           # Total number of instructions (2 digits, zero-padded)
<machine_word>        # One 4-digit word per instruction (e.g., 0312)
...
<data_size>           # Data memory allocation (from .ALLOC)
<data_value>          # One 4-digit value per .DATA variable, in declaration order
...
```

### `.hll` Listing File

```
HLX Assembler vX.X  |  source: prog.hal  |  output: prog.hlx
--- DATA ---
<daddr>  <value>  <original .DATA source line>
--- CODE ---
<iaddr>  <machine_word>  <original instruction source line>
```

---

## Error Reporting

Errors are written to **stderr** in the format:

```
filename.hal:LINE: ERROR Exxx: description
```

**Examples:**

```
prog.hal:7:  ERROR E002: No .BEGIN directive found
prog.hal:12: ERROR E020: Undefined data variable 'X' -- address 99 used
prog.hal:19: ERROR E021: Undefined label 'LOOP' -- address 99 used
```

Fatal errors halt assembly after the current phase. Non-fatal errors are collected and reported together so programmers can fix multiple issues in one pass.

---

## Project Structure

```
hlx-assembler/
├── src/
│   ├── main.py
│   ├── lexer.py
│   ├── parser.py
│   ├── pass1.py
│   ├── opcode_table.py
│   ├── pass2.py
│   ├── output.py
│   └── errors.py
├── tests/
│   ├── positive/          # Valid .hal programs with expected .hlx/.hll output
│   └── negative/          # Invalid programs with expected error codes
├── programs/              # Sample Halix assembly programs
├── docs/
│   ├── SRS-HLX-001.pdf    # Software Requirements Specification
│   └── SDD-HLX-002.pdf    # Software Design Document
├── halix_v25.opcode       # Opcode table (mnemonic → 2-digit code)
└── README.md
```

---

## Halix Architecture Quick Reference

| Property | Value |
|----------|-------|
| Architecture | Single-accumulator (one-address); only programmer-visible register is `ACC` |
| Word size | 4 decimal digits (this is a **decimal** machine, not binary) |
| Instruction format | `[opcode 2 digits][operand 2 digits]` — always exactly 4 digits |
| Instruction memory | Separate from data memory; addresses `00`–`99`; execution starts at `00` |
| Data memory | Separate from instruction memory; addresses `00`–`99`; size set by `.ALLOC` |
| Instruction count | 60 instructions (opcodes `00`–`58`, `59`, and `99`) |
| Termination | `HALT` instruction (opcode `99`); sets IP to `-99` |
| Label syntax | `LABEL:` at definition; `LABEL` (no colon) as operand |
| Comments | Begin with `#`; ignored by the assembler |

---

## Running the Tests

Test programs are located in `tests/positive/` (expected to assemble cleanly) and `tests/negative/` (expected to produce specific error codes).

```bash
# Run all tests (once test runner is in place)
python3 -m pytest tests/

# Manually assemble a single test case
python3 src/main.py tests/positive/first.hal
```

Expected `.hlx` and `.hll` output files are stored alongside each test case for diff-based validation against the reference assembler `HASM_v25.csh`.

---

## Team

| Role | Members |
|------|---------|
| **Development** | Frank Junior Hoza Logfor, Javonte Carter |
| **QA / Testing** | Ruxandra, Elizabeth |

**Course:** CEN 5075 — Software Systems Engineering, Florida A&M University  
**Reference assembler:** `HASM_v25.csh` by Prof. Jones
