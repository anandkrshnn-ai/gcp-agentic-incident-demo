# Project Limitations

This document lists **25 real, concrete limitations** of the tools provided in this repository. This project is a simple educational demo and is not hardened for production workflows.

## Git Churn Analyzer Limitations

1. **Host Git Dependency**: Relies on a local `git` installation being present on the system path; it fails if `git` is missing.
2. **Path Sensitivity**: Must be run from the root of a Git repository; running from subfolders or uninitialized directories results in program exit.
3. **Fixed Metric Weights**: Risk score uses hardcoded arbitrary weights (40% churn, 60% commit count) that cannot be adjusted dynamically.
4. **No AST Parsing**: Only calculates simple line counts instead of parsing an Abstract Syntax Tree (AST) to measure cyclomatic complexity.
5. **Ignores Binary Files**: Completely skips binary files and assets marked with `-` in `git log --numstat`.
6. **No Branch Awareness**: Analyzes the current checked-out branch only; it does not compare master/main branches to developer PR branches.
7. **Scale Bottleneck**: For very large repositories with hundreds of thousands of commits, running `git log` output into a Python string can cause memory exhaustion.
8. **Simple Renaming Logic**: Does not follow file renaming history, potentially treating a renamed file as a completely new file and resetting its history.
9. **Author Blindness**: Does not differentiate between changes made by principal authors and automated tools/linters.

## Test Generator Limitations

10. **Prompt Injection Risk**: Natural language feature descriptions are concatenated directly into the prompt without input sanitization or filtering.
11. **No AST Validation**: Does not verify if the generated code is syntactically correct Python/JavaScript before presenting it to the user.
12. **Static Mock Fallbacks**: Local offline fallback returns static, hardcoded mock templates that do not match the user's input request.
13. **Primitive Markdown Stripping**: Strips markdown backticks using basic string replacement, which fails if the generated code contains triple backticks.
14. **Single-Attempt Execution**: Lacks an evaluation loop to test, lint, and repair the generated code if it contains syntax or runtime errors.
15. **No Local Sandbox**: Running generated Playwright/pytest scripts runs directly on the host machine without containerized isolation.
16. **No Token Budgeting**: Does not calculate input/output token usage, risking API payload limit errors on very large inputs.

## Log Analyzer Limitations

17. **Basic Heuristics**: Log context extraction relies on naive string matches (`Traceback`, `at `, `Exception:`) and fails on interleaved, multi-threaded, or unstructured log formats.
18. **Truncated Stack Traces**: Arbitrarily captures up to 20 lines, which can discard critical error frames from deep stack traces.
19. **Context-Blind RCA**: The API prompt contains only the log snippet; it has no access to repository source code, environment variables, or dependency versions.
20. **No Auto-remediation**: Suggestions must be manually reviewed and copy-pasted; the tool cannot edit files or submit code fixes automatically.
21. **No Multilingual Support**: Fallback offline parser only recognizes generic English traceback keywords.

## General System & API Limitations

22. **Gemini API Key Dependency**: Requires a valid `GEMINI_API_KEY` environment variable. If missing, the tools degrade to basic offline heuristics.
23. **Strict Network Timeout**: Hardcoded 30-second HTTP request timeout with no retry backoff logic.
24. **Naive Error Catching**: Only catches `requests.exceptions.RequestException`, crash-failing on invalid JSON response bodies or payload schema changes.
25. **No Local Cache**: Does not cache API requests, resulting in redundant API calls and costs for identical logs or feature prompts.
