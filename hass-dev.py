#!/usr/bin/env python3
"""
ZipAssist CMMS Development CLI

This is the main development interface for contributors.
All commands delegate to the centralized tools/commands.py script.
"""

import sys
from pathlib import Path

# Add tools directory to path so we can import commands
tools_dir = Path(__file__).parent / "tools"
sys.path.insert(0, str(tools_dir))

try:
    from commands import (
        format_code,
        full_check,
        lint_code,
        quality_check,
        run_tests,
        setup_environment,
    )
except ImportError:
    print("❌ Could not import development commands.")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(
            """
🛠️  ZipAssist CMMS Development CLI

Usage: python hass-dev <command>

Commands:
  setup        - Set up development environment (run this first!)
  format       - Format code with ruff
  lint         - Run linting checks (advisory mode)
  lint-strict  - Run linting checks (strict mode)
  test         - Run the test suite with pytest
  quality      - Run format + lint (no tests)
  check        - Run all checks (format + lint + test)
  check-strict - Run all checks with strict type checking

Examples:
  python hass-dev setup       # First-time setup
  python hass-dev format      # Just format the code
  python hass-dev quality     # Quick quality check (no tests)
  python hass-dev check       # Full check before committing

💡 Tip: Use 'quality' for quick feedback, 'check' before committing
        """
        )
        return

    action = sys.argv[1].lower()

    if action == "setup":
        success = setup_environment()
    elif action == "format":
        success = format_code()
    elif action == "lint":
        success = lint_code(strict=False)
    elif action == "lint-strict":
        success = lint_code(strict=True)
    elif action == "test":
        success = run_tests()
    elif action == "quality":
        success = quality_check(strict=False)
    elif action == "check":
        success = full_check(strict=False)
    elif action == "check-strict":
        success = full_check(strict=True)
    else:
        print(f"❌ Unknown command: {action}")
        print("Run 'python hass-dev' without arguments to see available commands.")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()