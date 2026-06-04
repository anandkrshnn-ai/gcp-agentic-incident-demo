# Git Churn Analyzer Limitations

This document lists the concrete technical limitations of the `git_churn_analyzer.py` tool.

1. **System Git Dependency**
   The tool relies on the local execution of the `git` binary. If `git` is not installed or not available in the system's `PATH`, the subprocess execution fails and halts the tool.

2. **Git Repository Context Required**
   The script must be run within a valid initialized Git repository (or passed a path to one). If executed outside a repository, the `git log` command fails.

3. **Python-Only AST Analysis**
   AST complexity extraction is implemented strictly for Python (`.py`) files using Python's native `ast` module. Any other file types (e.g., Markdown, YAML, Shell scripts) return a baseline complexity score of `0`.

4. **Rename History Disconnection**
   To prevent parsing errors caused by complex git rename formats (like `{old => new}/file.py`), the command runs with the `--no-renames` flag. Consequently, renamed files are treated as a deletion of the old path and the creation of a new path, resetting the historical decay metrics for that file.

5. **Static Weight Distribution**
   The risk scoring algorithm uses hardcoded, static weights (40% normalized decayed churn, 60% normalized decayed commit frequency, and up to a 20-point addition for AST complexity). These weights are not dynamically adjustable based on repository patterns.

6. **Memory Scale Limits**
   The tool reads the entire command output of `git log` into memory as a single Python string. For extremely large repositories containing millions of commits and high file churn, this approach can lead to significant memory consumption.

7. **System Clock Skew Sensitivity**
   Age calculations depend on the UNIX timestamp stored in git commits. If developer machines have incorrect system clocks or spoofed dates, the computed age might be inaccurate. The tool mitigates negative ages by capping them at `0`, but future-dated commits will calculate zero decay.

8. **No Persistent Cache**
   Every run performs a complete git log traversal and parses the AST of all matching files on disk. There is no cache or state serialization to accelerate subsequent runs.

9. **Author and Bot Blindness**
   The analyzer calculates churn indiscriminately across all commits. Major automated refactors, formatting tools, linters, or package update bots (e.g., Dependabot) will inflate a file's decayed churn and commit metrics just as real human feature updates would.
