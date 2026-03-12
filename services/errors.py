"""
errors.py
---------
Centralized error reporting for the Halix assembler.

Design document alignment:
  - Shared AssemblerError dataclass
  - Unified formatting to stderr
  - Consistent error code + exit behavior
"""

from dataclasses import dataclass
import sys
from typing import Optional

ANSI_RED = "\033[31m"
ANSI_RESET = "\033[0m"


@dataclass
class AssemblerError:
    code: str
    message: str
    line: int
    filename: str
    is_fatal: bool


class ErrorHandler:
    def __init__(self, default_filename: str = "") -> None:
        self.default_filename = default_filename
        self.errors: list[AssemblerError] = []

    def report(
        self,
        code: str,
        message: str,
        line: int = 0,
        filename: Optional[str] = None,
        is_fatal: bool = True,
    ) -> AssemblerError:
        err = AssemblerError(
            code=code,
            message=message,
            line=line,
            filename=(filename if filename is not None else self.default_filename),
            is_fatal=is_fatal,
        )
        self.errors.append(err)
        return err

    def _format_error(self, err: AssemblerError) -> str:
        fname = err.filename if err.filename else "<unknown>"
        lineno = str(err.line) if err.line > 0 else "0"
        return f"{fname}:{lineno}: ERROR {err.code}: {err.message}"

    def emit(self, *, stream=None) -> None:
        if stream is None:
            stream = sys.stderr
        for err in self.errors:
            print(color_error(self._format_error(err)), file=stream)

    def has_fatal(self) -> bool:
        return any(err.is_fatal for err in self.errors)

    def emit_and_exit(self, exit_code: int) -> None:
        self.emit()
        raise SystemExit(exit_code)


def color_error(message: str) -> str:
    return f"{ANSI_RED}{message}{ANSI_RESET}"
