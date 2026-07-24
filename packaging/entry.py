"""PyInstaller entry point for the reimap desktop binary.

Kept separate from the package so the frozen build has a clean, importable
top-level script. Delegates immediately to the real CLI.
"""

from __future__ import annotations

import multiprocessing

from reimap.app import main

if __name__ == "__main__":
    # Required so frozen builds don't re-spawn the whole app on some platforms.
    multiprocessing.freeze_support()
    raise SystemExit(main())
