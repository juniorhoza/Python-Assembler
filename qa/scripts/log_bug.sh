#!/bin/bash
# =============================================================================
# HLX Assembler QA - Bug Logger
# Usage: ./qa/scripts/log_bug.sh
# =============================================================================

LOGS_DIR="./qa/logs"
BUG_LOG="$LOGS_DIR/BUG_LOG.md"
mkdir -p "$LOGS_DIR"

if [ -f "$BUG_LOG" ]; then
    LAST_ID=$(grep -o 'BUG-[0-9]*' "$BUG_LOG" | tail -1 | grep -o '[0-9]*')
    NEXT_NUM=$((${LAST_ID:-0} + 1))
else
    NEXT_NUM=1
    echo "# HLX Assembler Bug Log" > "$BUG_LOG"
    echo "**Project:** HLX Assembler | **QA Lead:** $(git config user.name 2>/dev/null)" >> "$BUG_LOG"
    echo "" >> "$BUG_LOG"
fi

BUG_ID=$(printf "BUG-%03d" $NEXT_NUM)
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo ""
echo "======================================================"
echo " Logging new bug: $BUG_ID"
echo " Branch: $BRANCH | Commit: $COMMIT"
echo "======================================================"
echo ""

read -p "TC ID (e.g. TC-DIR-001b): " TC_ID
read -p "Bug title (short description): " TITLE
read -p "Severity (Critical/High/Medium/Low): " SEVERITY
read -p "Steps to reproduce: " STEPS
read -p "Expected result: " EXPECTED
read -p "Actual result: " ACTUAL
read -p "Your name: " TESTER

cat >> "$BUG_LOG" << EOF

---

## $BUG_ID — $TITLE

| Field | Value |
|---|---|
| **Bug ID** | $BUG_ID |
| **TC ID** | $TC_ID |
| **Severity** | $SEVERITY |
| **Status** | Open |
| **Branch** | $BRANCH |
| **Commit** | $COMMIT |
| **Date** | $TIMESTAMP |
| **Tester** | $TESTER |

**Steps to Reproduce:**
$STEPS

**Expected Result:**
$EXPECTED

**Actual Result:**
$ACTUAL

**Fix Notes:** *(dev team fills this in)*

EOF

echo ""
echo "======================================================"
echo " Bug logged: $BUG_ID"
echo " Saved to  : $BUG_LOG"
echo "======================================================"
echo ""
echo "Next: commit and push:"
echo "  git add qa/logs/BUG_LOG.md"
echo "  git commit -m \"QA: Log $BUG_ID - $TITLE [$TC_ID]\""
echo "  git push origin qa/sprint-1"
