# Git Churn Analyzer Limitations & Architectural Flaws

This document details the concrete limitations, assumptions, and architectural constraints of the `git_churn_analyzer.py` tool.

---

## 1. Statistical and Modeling Assumptions

### Log-Transformation Compression
- **The Issue**: To handle power-law distributions, the tool applies a log-transformation ($y = \ln(x + 1)$) to raw metrics before scaling.
- **The Reality**: Log-transformation compresses the relative distance between high values. 
- **The Consequence**: The difference between a file with 1,000 commits and a file with 10,000 commits is compressed significantly in log space. This can under-represent the absolute danger of extreme outliers in large codebases.

### Zero-MAD Uniformity Fallback
- **The Issue**: Robust Z-scores use Median Absolute Deviation (MAD) as the divisor. 
- **The Reality**: In codebases where more than 50% of the files have identical metrics (e.g., most files have 0 commits in the specified time window, or most files have 0 complexity), the calculated MAD will be exactly `0.0`.
- **The Consequence**: When MAD is `0.0`, the tool falls back to standard standard-deviation Z-scores. If standard deviation is also `0.0` (all files are identical), all files receive a Z-score of `0.0`, rendering the relative risk ranking flat (every file is placed at exactly the 50.0% percentile).

### Gaussian Mapping of Non-Gaussian Data
- **The Issue**: Standardized composite Z-scores are mapped to a percentile using a normal Cumulative Distribution Function (CDF).
- **The Reality**: Even after log-transformation, composite scores may not fit a perfect Gaussian (normal) distribution.
- **The Consequence**: The reported percentile (e.g., `95.0%`) is a mathematical normalization to aid human interpretation, not a formal probability calculation.

---

## 2. Complexity Analysis & AST Limits

### Indentation-Based Fallback Heuristics
- **The Issue**: For non-Python files, the tool falls back to a generic complexity estimator that scans indentation shifts and keywords.
- **The Reality**: The fallback parser does not construct an AST.
- **The Consequence**: It can be easily fooled by multi-line strings, large blocks of commented-out code, minified source files, or formatting variations (e.g., switching between spaces and tabs).

### Python AST Dependency
- **The Issue**: Full semantic/syntactic complexity analysis is only supported for Python (`.py`) files.
- **The Reality**: Non-Python files rely on the generic fallback estimator, which has lower fidelity.
- **The Consequence**: Comparison of risk metrics between a Python file and a TypeScript file is structurally unbalanced.

---

## 3. Git & OS Subprocess Integration

### Shell/Path Dependency on Git Binary
- **The Issue**: The script spawns the shell-level `git` binary using Python's `subprocess` module.
- **The Reality**: The tool requires the CLI binary to be installed on the host and accessible via the system `PATH`.
- **The Consequence**: It will crash-fail if run in restricted container environments or if permission errors block subprocess spawning.

### Rename History Disconnection (`--no-renames`)
- **The Issue**: To prevent parser failures when reading git's rename output formats (e.g., `src/{old => new}/main.py`), the command forces the `--no-renames` flag.
- **The Reality**: Disabling rename detection treats file renaming as a deletion of the old path followed by the creation of a new path.
- **The Consequence**: The historical decay statistics (past commits and churn accumulated under the old file name) are decoupled from the new file path, resetting its computed risk.

---

## 4. Performance & Scaling Bottlenecks

### Single-Threaded synchronous Parsing
- **The Issue**: All file access, git history parsing, and AST parsing are done sequentially on a single thread.
- **The Reality**: Extremely large codebases with tens of thousands of source files will encounter execution delays.
- **The Consequence**: Bottlenecks are expected during initial log processing and AST generation.

### Contiguous Memory Buffering
- **The Issue**: The tool reads the entire command stdout of `git log` into host RAM as a single string.
- **The Reality**: Large codebases can generate multi-gigabyte log strings.
- **The Consequence**: Running this tool on massive codebases can lead to out-of-memory (OOM) process termination.
