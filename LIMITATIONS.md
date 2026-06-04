# Git Churn Analyzer Limitations & Architectural Flaws

This document details the concrete limitations, assumptions, and architectural constraints of the `git_churn_analyzer.py` tool.

---

## 1. Statistical and Modeling Assumptions

### Non-Normal Distribution (Power-Law / Pareto Distortions)
- **The Issue**: The risk scoring algorithm maps standardized composite Z-scores to a percentile scale `[0%, 100%]` using the Cumulative Distribution Function (CDF) of the standard normal distribution (`math.erf`).
- **The Reality**: Codebase metrics (churn, commits, complexity) naturally follow **heavy-tailed power-law distributions** (e.g., Pareto/Zipf's law), where a tiny fraction of files absorb the vast majority of changes. 
- **The Consequence**: Forcing a power-law distribution into a Gaussian (Normal) CDF projection produces skewed relative rankings. In small repositories or repositories dominated by a single massive file, standard deviation spikes, which artificially pushes moderate-risk files toward the median (50% risk percentile) and minimizes the visual risk gap between them.

### Outlier Sensitivity (Z-score Distortions)
- **The Issue**: Z-score calculation is highly sensitive to extreme outliers.
- **The Reality**: If a single file undergoes a massive refactoring event (e.g., adding 20,000 lines of configuration or moving a vendor script), its decayed churn will be multiple orders of magnitude larger than other files. 
- **The Consequence**: This outlier artificially inflates the population's mean and standard deviation. As a result, other truly high-risk source code files will have their Z-scores suppressed, making them appear closer to the average than they actually are.

---

## 2. Git & OS Subprocess Integration

### Hard Dependency on Host `git` Binary
- **The Issue**: The tool spawns shell processes using `subprocess.check_output`.
- **The Reality**: It requires a fully configured, native `git` CLI installed on the host machine and accessible via the system environment variables (`PATH`).
- **The Consequence**: Lacking library-level git bindings (like `GitPython` or `pygit2`), the tool crashes immediately if `git` is absent, locked, or restricted by OS permissions.

### Rename History Disconnection (`--no-renames`)
- **The Issue**: To prevent parser failures when reading git's complex rename representations (e.g., `src/{old => new}/main.py`), the command forces the `--no-renames` flag.
- **The Reality**: Disabling rename detection treats file renaming as a deletion of the old path followed by the creation of a new path.
- **The Consequence**: The historical decay statistics (past commits and churn accumulated under the old file name) are completely decoupled from the new file path, resetting its computed risk to near-zero.

---

## 3. Abstract Syntax Tree (AST) Limits

### Language Lock-In (Python Only)
- **The Issue**: AST analysis is built entirely on Python's native `ast` module.
- **The Reality**: The parser only scans files ending in `.py`.
- **The Consequence**: All other files (JavaScript, TypeScript, Go, YAML, HCL, Dockerfiles) bypass AST inspection entirely, defaulting to an AST complexity score of `0`. In polyglot codebases, risk evaluation will be heavily biased against Python files relative to other languages.

### Semantic Blindness
- **The Issue**: The cyclomatic-style complexity score is a simple counter of branching AST nodes (`If`, `IfExp`, `For`, `While`, `ExceptHandler`, `With`, `BoolOp`, `comprehension` ifs).
- **The Reality**: The tool cannot evaluate context. A cleanly written, long sequence of simple conditional statements is scored exactly the same as a nested, unreadable, spaghetti-code sequence.
- **The Consequence**: The AST score measures structural density, not code quality, design pattern health, or readability.

---

## 4. Performance & Scaling Bottlenecks

### Single-Threaded CPU Execution
- **The Issue**: Metric calculation and AST parsing occur synchronously on a single thread.
- **The Reality**: The script walks directories and calls AST parsers one file at a time.
- **The Consequence**: For massive corporate repositories with tens of thousands of Python files, analysis will bottleneck on CPU-bound AST operations.

### In-Memory Buffering
- **The Issue**: The stdout of `git log` is read into host RAM as a single contiguous string.
- **The Reality**: A codebase with hundreds of thousands of commits will generate multi-gigabyte log strings.
- **The Consequence**: Running this tool on massive codebases or containers with low memory configurations can lead to out-of-memory (OOM) process termination.

### Lack of State Cache
- **The Issue**: The analyzer has no serialization framework or local database cache (e.g., SQLite).
- **The Reality**: Every execution requires running `git log` and rebuilding the AST representation of all files from scratch.
- **The Consequence**: Running the tool repeatedly (e.g., in a CI/CD pipeline or git commit hook) consumes redundant CPU cycles.
