import subprocess
import os
import sys

def analyze_git_churn():
    """
    Analyzes local Git history using `git log --numstat` to calculate:
    1. Churn (total lines added + deleted per file)
    2. Commit frequency (how often a file is modified)
    3. Simple risk score based on actual metrics.
    """
    print("--- Git Churn & Risk Analyzer ---")
    
    # 1. Run git log --numstat
    try:
        output = subprocess.check_output(
            ["git", "log", "--numstat", "--pretty=format:"],
            stderr=subprocess.DEVNULL,
            text=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[Error] Failed to execute git commands: {e}", file=sys.stderr)
        print("Please ensure you are in a git repository and git is installed.", file=sys.stderr)
        sys.exit(1)

    # 2. Parse stat output
    stats = {}
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) == 3:
            added_str, deleted_str, filepath = parts
            # Skip binary files represented by '-'
            if added_str == '-' or deleted_str == '-':
                continue
            try:
                added = int(added_str)
                deleted = int(deleted_str)
            except ValueError:
                continue
            
            if filepath not in stats:
                stats[filepath] = {"churn": 0, "commits": 0}
            
            stats[filepath]["churn"] += (added + deleted)
            stats[filepath]["commits"] += 1

    if not stats:
        print("No commit history found or git log returned empty results.")
        return []

    # 3. Calculate Risk Score
    # Risk Score = (Normalized Churn * 0.4) + (Normalized Commits * 0.6)
    max_churn = max(f["churn"] for f in stats.values()) or 1
    max_commits = max(f["commits"] for f in stats.values()) or 1

    report = []
    for filepath, data in stats.items():
        norm_churn = data["churn"] / max_churn
        norm_commits = data["commits"] / max_commits
        risk_score = (norm_churn * 40.0) + (norm_commits * 60.0)
        
        report.append({
            "file": filepath,
            "churn": data["churn"],
            "commits": data["commits"],
            "risk_score": round(risk_score, 1)
        })

    # Sort by risk score descending
    report.sort(key=lambda x: x["risk_score"], reverse=True)

    # 4. Output Markdown Report
    print("\n### Git Churn & Complexity Risk Report")
    print("-" * 75)
    print(f"{'File Path':<45} | {'Churn (Lines)':<13} | {'Commits':<8} | {'Risk Score':<10}")
    print("-" * 75)
    for r in report[:15]:  # Show top 15 risk files
        print(f"{r['file']:<45} | {r['churn']:<13} | {r['commits']:<8} | {r['risk_score']:<10}")
    print("-" * 75)
    print(f"Total files tracked: {len(report)}")
    return report

if __name__ == "__main__":
    analyze_git_churn()
