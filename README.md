# GCP Agentic Incident Demo

This is a **simple educational demo** showing basic integration of Gemini with git history analysis and log parsing. It is **not production ready** and contains no novel research or advanced AI techniques.

## Overview

This repository contains basic helper scripts to demonstrate:
1. **Git Churn Analyzer**: Analyzes local git commit history and diff stat size to identify files with high churn.
2. **Log Analyzer**: Parses log stack traces and uses Gemini to generate a basic root cause analysis (RCA) report.
3. **Test Generator**: Generates simple, runnable pytest or Playwright test files from natural language descriptions via Gemini.

## Structure

- [tools/git_churn_analyzer.py](file:///c:/Users/Admin/Documents/Github/gcp-agentic-incident-demo/tools/git_churn_analyzer.py) — Analyzes local git repository commit history.
- [tools/log_analyzer.py](file:///c:/Users/Admin/Documents/Github/gcp-agentic-incident-demo/tools/log_analyzer.py) — Parses log outputs and suggests fixes using Gemini.
- [tools/test_generator.py](file:///c:/Users/Admin/Documents/Github/gcp-agentic-incident-demo/tools/test_generator.py) — Generates verification scripts using Gemini.
- [integration/](file:///c:/Users/Admin/Documents/Github/gcp-agentic-incident-demo/integration) — Minimal pipeline integration examples for GitHub Actions and Azure DevOps.

## Setup & Configuration

Install dependencies:
```bash
pip install -r requirements.txt
```

Set the Gemini API Key:
```bash
export GEMINI_API_KEY="your-api-key"
```

## Running the Tools

1. **Git Churn Analyzer**:
   ```bash
   python tools/git_churn_analyzer.py
   ```
2. **Log Analyzer**:
   ```bash
   python tools/log_analyzer.py <path_to_log_file>
   ```
3. **Test Generator**:
   ```bash
   python tools/test_generator.py --feature "Verify user login page title is correct" --lang playwright
   ```
