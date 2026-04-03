#!/bin/bash
echo "======================================================"
echo " HLX Assembler QA Environment Setup"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"

if [ ! -d ".git" ]; then
    echo "ERROR: Run this from the repo root:"
    echo "  cd ~/workspace/Python-Assembler"
    echo "  ./qa/scripts/setup_env.sh"
    exit 1
fi
echo "OK - in repo: $(basename $(pwd))"

sudo apt-get install -y csh
command -v csh &>/dev/null && echo "OK - csh installed" || echo "ERROR: csh failed"

python3 --version

chmod +x qa/scripts/run_tests.sh
chmod +x qa/scripts/log_bug.sh
echo "OK - scripts executable"

mkdir -p qa/tests/inputs qa/tests/outputs/student qa/tests/outputs/reference qa/logs qa/docs
echo "OK - folders ready"

echo "======================================================"
echo " Setup complete! Next steps:"
echo "  1. Add HASM_v25.csh to qa/scripts/ (get from professor)"
echo "  2. Run tests: ./qa/scripts/run_tests.sh"
echo "  3. Log bugs:  ./qa/scripts/log_bug.sh"
echo "======================================================"
