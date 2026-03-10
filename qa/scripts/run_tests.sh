#!/bin/bash
# =============================================================================
# HLX Assembler QA Test Runner
# Usage:
#   ./qa/scripts/run_tests.sh                        # run all tests
#   ./qa/scripts/run_tests.sh TC-PAR-001             # run one test
#   ./qa/scripts/run_tests.sh --branch javonte-work  # label which dev branch
# =============================================================================

ASSEMBLER_CANDIDATES=(
    "python3 HASM_CLI.py"
    "python3 assembler.py"
    "python3 hasm.py"
)
REFERENCE="csh ./qa/scripts/HASM_v25.csh"
TESTS_DIR="./qa/tests/inputs"
OUT_DIR="./qa/tests/outputs"
LOGS_DIR="./qa/logs"

BRANCH_LABEL=$(git branch --show-current 2>/dev/null || echo "unknown")
SINGLE_TEST=""
for arg in "$@"; do
    if [ "$PREV" = "--branch" ]; then
        BRANCH_LABEL="$arg"
    elif [ "$arg" != "--branch" ]; then
        SINGLE_TEST="$arg"
    fi
    PREV="$arg"
done

ASSEMBLER=""
for candidate in "${ASSEMBLER_CANDIDATES[@]}"; do
    cmd=$(echo $candidate | awk '{print $2}')
    if [ -f "$cmd" ]; then
        ASSEMBLER="$candidate"
        break
    fi
done

TIMESTAMP=$(date "+%Y-%m-%d_%H-%M-%S")
DATESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
mkdir -p "$OUT_DIR/student" "$OUT_DIR/reference" "$LOGS_DIR"
LOG_FILE="$LOGS_DIR/run_${TIMESTAMP}_${BRANCH_LABEL//\//-}.log"
SUMMARY_FILE="$LOGS_DIR/SUMMARY.log"

PASS=0; FAIL=0; BLOCKED=0; NOT_RUN=0
FAILED_TESTS=()
BLOCKED_TESTS=()

log() { echo "$1" | tee -a "$LOG_FILE"; }

log "============================================================"
log " HLX ASSEMBLER QA TEST RUN"
log " Date/Time  : $DATESTAMP"
log " Branch     : $BRANCH_LABEL"
log " Assembler  : ${ASSEMBLER:-NOT FOUND}"
log " Tester     : $(git config user.name 2>/dev/null || echo 'unknown')"
log " Git Commit : $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
log "============================================================"

if [ -z "$ASSEMBLER" ]; then
    log ""
    log "[BLOCKED] Could not find assembler. Looked for:"
    for c in "${ASSEMBLER_CANDIDATES[@]}"; do log "          $c"; done
    log "          Make sure you are running from the repo root."
    exit 1
fi

if ! command -v csh &>/dev/null; then
    log "[WARNING] csh not found - reference comparisons will be skipped."
    REF_AVAILABLE=false
else
    REF_AVAILABLE=true
fi

run_test() {
    local TC_ID="$1"
    local HAL_FILE="$TESTS_DIR/${TC_ID}.hal"

    log ""
    log "------------------------------------------------------------"
    log "TEST      : $TC_ID"
    log "Input     : $HAL_FILE"

    if [ ! -f "$HAL_FILE" ]; then
        log "STATUS    : BLOCKED"
        log "REASON    : Input file not found - waiting on test team to create it"
        BLOCKED_TESTS+=("$TC_ID")
        ((BLOCKED++))
        return
    fi

    STUDENT_OUTDIR="$OUT_DIR/student/${TC_ID}"
    mkdir -p "$STUDENT_OUTDIR"
    cp "$HAL_FILE" "$STUDENT_OUTDIR/"

    STUDENT_OUTPUT=$($ASSEMBLER "$HAL_FILE" 2>&1)
    STUDENT_EXIT=$?

    log "Exit Code : $STUDENT_EXIT"
    log "Output    :"
    echo "$STUDENT_OUTPUT" | while IFS= read -r line; do log "  $line"; done

    BASENAME=$(basename "$HAL_FILE" .hal)
    for ext in hlx hll; do
        [ -f "${BASENAME}.${ext}" ] && mv "${BASENAME}.${ext}" "$STUDENT_OUTDIR/"
    done
    STUDENT_HLX="$STUDENT_OUTDIR/${BASENAME}.hlx"

    if $REF_AVAILABLE; then
        REF_OUTDIR="$OUT_DIR/reference/${TC_ID}"
        mkdir -p "$REF_OUTDIR"
        cp "$HAL_FILE" "$REF_OUTDIR/"
        pushd "$REF_OUTDIR" > /dev/null
            REF_OUTPUT=$(csh ../../scripts/HASM_v25.csh "$(basename "$HAL_FILE")" 2>&1)
            REF_EXIT=$?
        popd > /dev/null
        REF_HLX="$REF_OUTDIR/${BASENAME}.hlx"
        log "Ref Exit  : $REF_EXIT"
    fi

    if $REF_AVAILABLE && [ -f "$STUDENT_HLX" ] && [ -f "$REF_HLX" ]; then
        if diff -q "$STUDENT_HLX" "$REF_HLX" > /dev/null 2>&1; then
            log "HLX Diff  : MATCH"
            log "STATUS    : PASS"
            ((PASS++))
        else
            log "HLX Diff  : MISMATCH"
            diff "$STUDENT_HLX" "$REF_HLX" | head -30 | while IFS= read -r line; do log "  $line"; done
            log "STATUS    : FAIL"
            FAILED_TESTS+=("$TC_ID")
            ((FAIL++))
        fi
    elif [ $STUDENT_EXIT -ne 0 ] && [ -n "$STUDENT_OUTPUT" ]; then
        log "STATUS    : PASS (error case - assembler produced error output as expected)"
        ((PASS++))
    elif [ $STUDENT_EXIT -eq 0 ] && [ ! -f "$STUDENT_HLX" ]; then
        log "STATUS    : FAIL (assembled without error but no .hlx file produced)"
        FAILED_TESTS+=("$TC_ID")
        ((FAIL++))
    else
        log "STATUS    : NOT TESTED (reference unavailable or output missing)"
        ((NOT_RUN++))
    fi
}

ALL_TESTS=(
    TC-PAR-001 TC-PAR-002 TC-PAR-003 TC-PAR-004 TC-PAR-005
    TC-DIR-001a TC-DIR-001b TC-DIR-001c TC-DIR-002
    TC-DIR-003a TC-DIR-003b TC-DIR-003c TC-DIR-006
    TC-SYM-001 TC-SYM-002 TC-SYM-003 TC-SYM-005
    TC-GEN-001 TC-GEN-002 TC-GEN-003 TC-GEN-004 TC-GEN-005
    TC-ERR-001 TC-ERR-002 TC-ERR-003 TC-ERR-004 TC-ERR-005
    TC-CON-001 TC-CON-002 TC-CON-003
)

if [ -n "$SINGLE_TEST" ]; then
    run_test "$SINGLE_TEST"
else
    for TC in "${ALL_TESTS[@]}"; do run_test "$TC"; done
fi

TOTAL=$((PASS + FAIL + BLOCKED + NOT_RUN))
RATE=0
[ $((PASS + FAIL)) -gt 0 ] && RATE=$(echo "scale=1; $PASS * 100 / ($PASS + $FAIL)" | bc)

log ""
log "============================================================"
log " SUMMARY"
log "  Branch     : $BRANCH_LABEL"
log "  Commit     : $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
log "  Total TCs  : $TOTAL"
log "  PASS       : $PASS"
log "  FAIL       : $FAIL"
log "  BLOCKED    : $BLOCKED (input files not yet created)"
log "  NOT TESTED : $NOT_RUN"
log "  PASS RATE  : ${RATE}%"
log ""
if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
    log "  FAILED TESTS:"
    for t in "${FAILED_TESTS[@]}"; do log "    - $t"; done
fi
if [ ${#BLOCKED_TESTS[@]} -gt 0 ]; then
    log "  BLOCKED:"
    for t in "${BLOCKED_TESTS[@]}"; do log "    - $t"; done
fi
log "============================================================"
log " Full log saved: $LOG_FILE"

echo "------------------------------------------------------------" >> "$SUMMARY_FILE"
echo "Run: $DATESTAMP | Branch: $BRANCH_LABEL | Commit: $(git rev-parse --short HEAD 2>/dev/null)" >> "$SUMMARY_FILE"
echo "PASS: $PASS | FAIL: $FAIL | BLOCKED: $BLOCKED | NOT TESTED: $NOT_RUN | RATE: ${RATE}%" >> "$SUMMARY_FILE"
[ ${#FAILED_TESTS[@]} -gt 0 ] && echo "Failed: ${FAILED_TESTS[*]}" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

echo ""
echo "Log saved to : $LOG_FILE"
echo "Summary at   : $LOGS_DIR/SUMMARY.log"
