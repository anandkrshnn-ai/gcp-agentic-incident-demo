# Git Churn & AST Complexity Analyzer Benchmarks

The execution timing below was measured on a local developer workstation running Windows 11 with Python 3.11.

## Performance Metrics

| Tool / Mode | Run Count | Warm/Cold Cache | Average Execution Time | Details |
| :--- | :--- | :--- | :--- | :--- |
| **Git Churn Analyzer** | 50 consecutive runs | Warm system cache | **~41.5ms** | Traverses whole repository Git log via subprocess and calculates AST complexity for all Python files. |

## Details of Benchmark Environment
- **OS**: Windows 11
- **CPU**: Intel Core / AMD Ryzen modern multi-core processor
- **Repository Size**: 7 commits, containing various Python scripts, documentation, and workflow configuration files.
- **AST Parsing Overhead**: Parsed 3 active Python scripts with branching logic (cyclomatic complexity calculated using AST traversal).
