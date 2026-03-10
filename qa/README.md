# QA Environment — HLX Assembler
**QA Lead:** Ruxandra Flueras | **Sprint:** 1

## Folder Structure
```
qa/
├── scripts/
│   ├── setup_env.sh      <- Run ONCE to set up your machine
│   ├── run_tests.sh      <- Main test runner (auto-logs every run)
│   ├── log_bug.sh        <- Interactively log a bug
│   └── HASM_v25.csh      <- Reference assembler (get from professor)
├── tests/
│   ├── inputs/           <- .hal test files (one per TC ID)
│   └── outputs/          <- Auto-generated assembler output
├── logs/
│   ├── SUMMARY.log       <- One-line summary of every test run
│   ├── BUG_LOG.md        <- All logged bugs
│   └── run_TIMESTAMP.log <- Full log per run
└── docs/
    └── QA-HLX-001.docx   <- QA report
```

## Setup (run once)
```
cd ~/workspace/Python-Assembler
./qa/scripts/setup_env.sh
```

## Running Tests
Always run from the repo root.
```
# Run all tests
./qa/scripts/run_tests.sh

# Run one test
./qa/scripts/run_tests.sh TC-PAR-001

# Run against a specific dev branch
git checkout javonte-work
./qa/scripts/run_tests.sh --branch javonte-work

git checkout dev
./qa/scripts/run_tests.sh --branch dev
```

## Logging a Bug
When a test fails, run:
```
./qa/scripts/log_bug.sh
```
It asks you questions and saves the bug to qa/logs/BUG_LOG.md.

## Test Input File Naming
Files must be named exactly after the TC ID:
- TC-PAR-001.hal
- TC-DIR-001b.hal
- TC-DIR-003b.hal

If a file does not exist yet, the runner marks it BLOCKED (not a failure).

## Saving Your Work
```
git add qa/
git commit -m "QA: describe what you did"
git push origin qa/sprint-1
```
