# src/utils/output_manager.py
"""Shared output utilities for PL/0 Compiler modules.

Provides:
- resolve_output_path(input_path) -- maps input file path to output file path
- TeeWriter -- duplicates writes to console + file
- tee_output(output_path) -- context manager for automatic file mirroring
"""

import os
import sys


def resolve_output_path(input_path):
    """Map an input file path to the corresponding output file path.

    Given an input like 'input/correct/lexer.txt', returns:
      '<project_root>/output/correct/lexer.txt'

    Rules:
    - If input_path contains a 'correct' or 'error' directory segment,
      the output subdirectory mirrors it.
    - Otherwise, defaults to 'correct'.
    - The output filename matches the input filename (stem preserved).

    Args:
        input_path: str, relative or absolute path to the input source file.

    Returns:
        str, absolute path to the output .txt file.
    """
    # Normalize separators for cross-platform consistency
    input_path = input_path.replace('\\', '/')

    # Determine project root: go up two levels from this file
    # src/utils/output_manager.py -> src -> project_root
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..')
    )

    # Determine subdirectory (correct vs error) from input path segments
    parts = input_path.split('/')
    subdir = 'correct'  # default
    if 'error' in parts:
        subdir = 'error'
    elif 'correct' in parts:
        subdir = 'correct'

    # Extract the input filename stem (e.g., "lexer" from "lexer.txt")
    basename = os.path.basename(input_path)
    stem, _ext = os.path.splitext(basename)

    # Build output directory and ensure it exists
    out_dir = os.path.join(project_root, 'output', subdir)
    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, f"{stem}.txt")
    return out_file


class TeeWriter:
    """File-like object that writes to both the original stdout and a file.

    Used to replace sys.stdout so that all print() calls are mirrored
    to a disk file while still appearing on the console.

    Delegates special attributes (encoding, reconfigure, fileno, isatty,
    close) to the original stdout to avoid breaking code that inspects
    or reconfigures sys.stdout.
    """

    def __init__(self, original_stdout, file_handle):
        self._original = original_stdout
        self._file = file_handle

    def write(self, data):
        self._original.write(data)
        self._file.write(data)

    def flush(self):
        self._original.flush()
        self._file.flush()

    def reconfigure(self, **kwargs):
        """Delegate to original stdout (used on Windows for UTF-8 setup)."""
        return self._original.reconfigure(**kwargs)

    def fileno(self):
        return self._original.fileno()

    def isatty(self):
        return self._original.isatty()

    @property
    def encoding(self):
        return getattr(self._original, 'encoding', 'utf-8')

    def close(self):
        """Close only the file, not the original stdout."""
        if self._file and not self._file.closed:
            self._file.close()


class tee_output:
    """Context manager that mirrors stdout to a file.

    Usage:
        with tee_output('output/correct/lexer.txt'):
            print('This goes to BOTH console and the file')

    If output_path is None, the context manager is a no-op (no file written).

    Creates parent directories automatically.
    Handles cleanup on exception (file is closed, stdout is restored).
    """

    def __init__(self, output_path):
        self._path = output_path
        self._file = None
        self._original_stdout = None
        self._tee = None

    def __enter__(self):
        if self._path is None:
            return self
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        self._file = open(self._path, 'w', encoding='utf-8')
        self._original_stdout = sys.stdout
        self._tee = TeeWriter(self._original_stdout, self._file)
        sys.stdout = self._tee
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._path is None:
            return False
        try:
            # Flush before restoring to avoid lost output
            if self._tee:
                self._tee.flush()
        finally:
            sys.stdout = self._original_stdout
            if self._file and not self._file.closed:
                self._file.close()
        return False  # do not suppress exceptions
