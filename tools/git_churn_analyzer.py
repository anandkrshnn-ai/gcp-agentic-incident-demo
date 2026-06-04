import subprocess
import os
import sys
import time
import math
import ast

def get_ast_complexity(filepath):
    """
    Calculates a cyclomatic-style complexity score for a Python file.
    It counts decision/branching points within the AST:
    - Conditionals (If, IfExp)
    - Loops (For, While)
    - Exception handling (ExceptHandler)
    - Context managers (With)
    - Logical operators (BoolOp/and/or)
    - Comprehension filters (ifs in list/dict/set comprehensions)
    """
    if not filepath.endswith(".py") or not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        
        # Base cyclomatic complexity of a file is 1 (linear flow)
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp, ast.For, ast.While, ast.ExceptHandler, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                # BoolOp has multiple values (e.g. 'a and b and c' -> 3 values, 2 branches)
                complexity += len(node.values) - 1
            elif isinstance(node, ast.comprehension):
                # Count conditions inside list/dict/set comprehensions (e.g. 'if x > 2')
                complexity += len(node.ifs)
        return complexity
    except Exception:
        return 0

def analyze_git_history(repo_path="."):
    """
    Parses git history with temporal decay:
    - Recent commits carry full weight.
    - Older commits decay exponentially based on a 30-day half-life.
    - Risk = (Decayed Churn * 0.4) + (Decayed Commits * 0.6) + (AST Complexity * 0.5)
    """
    print("Executing Git Churn & AST Complexity Analysis...")
    
    # Run git log with --no-renames to get flat addition/deletion paths instead of rename patterns
    try:
        raw_log = subprocess.check_output(
            ["git", "log", "--numstat", "--no-renames", "--pretty=format:COMMIT:%ct"],
            cwd=repo_path,
            stderr=subprocess.DEVNULL,
            text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error executing git command: {e}", file=sys.stderr)
        sys.exit(1)

    now = time.time()
    decay_lambda = math.log(2) / 30.0  # 30-day half-life decay factor
    stats = {}

    current_timestamp = None
    for line in raw_log.splitlines():
        line = line.strip()
        if not line:
            continue
        
        if line.startswith("COMMIT:"):
            try:
                current_timestamp = int(line.split(":")[1])
            except ValueError:
                current_timestamp = None
            continue

        if current_timestamp is None:
            continue

        parts = line.split("\t")
        if len(parts) == 3:
            added_str, deleted_str, filepath = parts
            if added_str == '-' or deleted_str == '-':
                continue  # Skip binary files
            
            try:
                added = int(added_str)
                deleted = int(deleted_str)
            except ValueError:
                continue

            # Calculate age in days
            age_days = (now - current_timestamp) / 86400.0
            if age_days < 0:
                age_days = 0  # Handle clock skew
            
            # Compute exponential decay weight
            weight = math.exp(-decay_lambda * age_days)
            churn = added + deleted

            if filepath not in stats:
                stats[filepath] = {"decayed_churn": 0.0, "decayed_commits": 0.0}

            stats[filepath]["decayed_churn"] += (churn * weight)
            stats[filepath]["decayed_commits"] += weight

    if not stats:
        print("No historical logs or commit records parsed.")
        return []

    # Normalize metrics and calculate risk
    max_churn = max(f["decayed_churn"] for f in stats.values()) or 1.0
    max_commits = max(f["decayed_commits"] for f in stats.values()) or 1.0

    report = []
    for filepath, data in stats.items():
        # Calculate actual AST complexity
        full_path = os.path.join(repo_path, filepath)
        complexity = get_ast_complexity(full_path)
        
        norm_churn = data["decayed_churn"] / max_churn
        norm_commits = data["decayed_commits"] / max_commits
        
        # Risk score calculation
        risk_score = (norm_churn * 40.0) + (norm_commits * 60.0)
        if complexity > 0:
            # Scale AST complexity: add up to 20 points based on complexity level
            risk_score += min(20.0, complexity * 0.5)

        report.append({
            "file": filepath,
            "decayed_churn": round(data["decayed_churn"], 1),
            "decayed_commits": round(data["decayed_commits"], 2),
            "complexity": complexity,
            "risk_score": round(risk_score, 1)
        })

    report.sort(key=lambda x: x["risk_score"], reverse=True)

    print("\n### Churn & Complexity Analysis Report")
    print("-" * 90)
    print(f"{'File Path':<40} | {'Decayed Churn':<13} | {'Decayed Commits':<15} | {'AST Complexity':<14} | {'Risk Score':<10}")
    print("-" * 90)
    for r in report[:15]:
        print(f"{r['file']:<40} | {r['decayed_churn']:<13} | {r['decayed_commits']:<15} | {r['complexity']:<14} | {r['risk_score']:<10}")
    print("-" * 90)
    return report

if __name__ == "__main__":
    analyze_git_history()
