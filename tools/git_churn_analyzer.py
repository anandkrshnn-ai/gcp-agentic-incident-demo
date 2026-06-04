import subprocess
import os
import sys
import time
import math
import ast
import argparse
import fnmatch

# =====================================================================
# Extensible Complexity Analyzer Registry (Plugin Pattern)
# =====================================================================

def get_python_complexity(filepath):
    """
    Calculates a cyclomatic-style complexity score for a Python file by counting branching points in the AST.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp, ast.For, ast.While, ast.ExceptHandler, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.comprehension):
                complexity += len(node.ifs)
        return complexity
    except Exception:
        return 0

def get_generic_complexity(filepath):
    """
    Fallback complexity analyzer for non-Python files.
    Calculates a primitive structural density score based on indentations and block structures.
    """
    if not os.path.exists(filepath):
        return 0
    try:
        score = 1
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # Count common control flow keywords and indentation shifts
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Check indentation level shifts (heuristically, tabs/spaces)
                indent = len(line) - len(line.lstrip())
                if indent >= 4:
                    score += indent // 4
                
                # Branch keyword heuristic matching
                words = line_stripped.split()
                if words:
                    first_word = words[0]
                    if first_word in ("if", "for", "while", "catch", "except", "case", "switch"):
                        score += 1
        return score
    except Exception:
        return 0

# Register complexity analyzers by file extension
COMPLEXITY_REGISTRY = {
    ".py": get_python_complexity,
}

def get_ast_complexity(filepath):
    """
    Dispatches file to its registered analyzer or falls back to a generic indicator.
    """
    ext = os.path.splitext(filepath)[1].lower()
    analyzer = COMPLEXITY_REGISTRY.get(ext, get_generic_complexity)
    return analyzer(filepath)

# =====================================================================
# Robust Statistical Scoring Model
# =====================================================================

def calculate_robust_z_scores(values, log_transform=True):
    """
    Calculates robust Z-scores using Median and Median Absolute Deviation (MAD).
    Optionally applies log-transformation (log1p) first to stabilize heavy-tailed (power-law) metrics.
    """
    n = len(values)
    if n == 0:
        return []
    
    # Log transform to compress power-law tails (only for non-negative raw metrics)
    if log_transform:
        log_values = [math.log1p(x) for x in values]
    else:
        log_values = list(values)
    
    # Helper to calculate median
    def get_median(lst):
        sorted_lst = sorted(lst)
        mid = len(sorted_lst) // 2
        if len(sorted_lst) % 2 == 1:
            return sorted_lst[mid]
        return (sorted_lst[mid - 1] + sorted_lst[mid]) / 2.0

    median = get_median(log_values)
    
    # Compute MAD (Median Absolute Deviation)
    abs_deviations = [abs(x - median) for x in log_values]
    mad = get_median(abs_deviations)
    
    # Scale factor (1.4826) makes MAD comparable to standard deviation under a normal distribution
    mad_std = 1.4826 * mad
    
    if mad_std == 0.0:
        # Fallback to standard deviation of log-transformed values if deviation is uniform
        mean = sum(log_values) / n
        variance = sum((x - mean) ** 2 for x in log_values) / n
        std_dev = math.sqrt(variance)
        if std_dev == 0.0:
            return [0.0] * n
        return [(x - mean) / std_dev for x in log_values]
    
    return [(x - median) / mad_std for x in log_values]

def normal_cdf(z):
    """
    Cumulative distribution function for standard normal distribution.
    Maps Z-score to a percentile [0.0, 1.0].
    """
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

# =====================================================================
# History Parsing and Main Flow
# =====================================================================

def analyze_git_history(args):
    """
    Parses git history with configurable temporal decay and calculates statistical risk.
    """
    print(f"Analyzing repository: {os.path.abspath(args.repo_path)}")
    
    cmd = ["git", "log", "--numstat", "--no-renames", "--pretty=format:COMMIT:%ct"]
    if args.time_window > 0:
        cmd.append(f"--since={args.time_window} days ago")

    try:
        raw_log = subprocess.check_output(
            cmd,
            cwd=args.repo_path,
            stderr=subprocess.DEVNULL,
            text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error executing git command: {e}", file=sys.stderr)
        sys.exit(1)

    now = time.time()
    decay_lambda = math.log(2) / args.half_life if args.half_life > 0 else 0.0
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
            
            if any(fnmatch.fnmatch(filepath, pattern) for pattern in args.exclude):
                continue
            
            if args.include and not any(fnmatch.fnmatch(filepath, pattern) for pattern in args.include):
                continue

            try:
                added = int(added_str)
                deleted = int(deleted_str)
            except ValueError:
                continue

            age_days = (now - current_timestamp) / 86400.0
            if age_days < 0:
                age_days = 0
            
            weight = math.exp(-decay_lambda * age_days) if decay_lambda > 0.0 else 1.0
            churn = added + deleted

            if filepath not in stats:
                stats[filepath] = {"decayed_churn": 0.0, "decayed_commits": 0.0}

            stats[filepath]["decayed_churn"] += (churn * weight)
            stats[filepath]["decayed_commits"] += weight

    if not stats:
        print("No historical logs or commit records parsed matching target criteria.")
        return []

    filepaths = list(stats.keys())
    decayed_churns = [stats[f]["decayed_churn"] for f in filepaths]
    decayed_commits = [stats[f]["decayed_commits"] for f in filepaths]
    
    complexities = []
    for f in filepaths:
        full_path = os.path.join(args.repo_path, f)
        complexities.append(get_ast_complexity(full_path))

    # Calculate robust, outlier-resistant Z-scores
    z_churns = calculate_robust_z_scores(decayed_churns)
    z_commits = calculate_robust_z_scores(decayed_commits)
    z_complexities = calculate_robust_z_scores(complexities)

    # Compute weighted composite score for each file
    raw_risks = []
    for i in range(len(filepaths)):
        score = (
            args.weight_churn * z_churns[i] +
            args.weight_commits * z_commits[i] +
            args.weight_complexity * z_complexities[i]
        )
        raw_risks.append(score)

    # Standardize composite score to final risk Z-score (do not log-transform composite Z-scores)
    final_z_scores = calculate_robust_z_scores(raw_risks, log_transform=False)

    report = []
    for i, filepath in enumerate(filepaths):
        z_final = final_z_scores[i]
        risk_percentile = normal_cdf(z_final) * 100.0
        
        report.append({
            "file": filepath,
            "decayed_churn": round(decayed_churns[i], 1),
            "decayed_commits": round(decayed_commits[i], 2),
            "complexity": complexities[i],
            "z_score": round(z_final, 2),
            "risk_percentile": round(risk_percentile, 1)
        })

    report.sort(key=lambda x: x["risk_percentile"], reverse=True)

    print("\n### Churn & Complexity Analysis Report")
    print("-" * 110)
    print(f"{'File Path':<40} | {'Decayed Churn':<13} | {'Decayed Commits':<15} | {'AST/Struct Comp':<15} | {'Risk Z-Score':<12} | {'Risk Percentile':<15}")
    print("-" * 110)
    for r in report[:args.limit]:
        print(f"{r['file']:<40} | {r['decayed_churn']:<13} | {r['decayed_commits']:<15} | {r['complexity']:<15} | {r['z_score']:+12.2f} | {r['risk_percentile']:>13.1f}%")
    print("-" * 110)
    return report

def main():
    parser = argparse.ArgumentParser(description="Git Churn & AST Complexity Analyzer")
    parser.add_argument("--repo-path", default=".", help="Path to the target Git repository")
    parser.add_argument("--half-life", type=float, default=30.0, help="Exponential decay half-life in days (0 to disable decay)")
    parser.add_argument("--time-window", type=int, default=0, help="Analyze commits only in the last N days (0 for all time)")
    parser.add_argument("--weight-churn", type=float, default=0.3, help="Risk score weight for decayed code churn (lines added/deleted)")
    parser.add_argument("--weight-commits", type=float, default=0.3, help="Risk score weight for decayed commit frequency")
    parser.add_argument("--weight-complexity", type=float, default=0.4, help="Risk score weight for AST complexity")
    parser.add_argument("--exclude", nargs="*", default=[], help="Glob patterns of files/directories to exclude")
    parser.add_argument("--include", nargs="*", default=[], help="Glob patterns of files/directories to include")
    parser.add_argument("--limit", type=int, default=15, help="Maximum number of files to show in the output table")
    
    args = parser.parse_args()
    
    total_weight = args.weight_churn + args.weight_commits + args.weight_complexity
    if total_weight > 0:
        args.weight_churn /= total_weight
        args.weight_commits /= total_weight
        args.weight_complexity /= total_weight
    
    analyze_git_history(args)

if __name__ == "__main__":
    main()
