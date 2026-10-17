"""Top-level PyInstaller entry point.

Uses absolute imports so the frozen EXE does not fail with
'attempted relative import with no known parent package'.
"""

from kings_grillz.app import main


if __name__ == "__main__":
    main()
