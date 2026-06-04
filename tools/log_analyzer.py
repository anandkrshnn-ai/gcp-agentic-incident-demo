import os
import re
import sys
import argparse
import requests

def extract_error_context(log_path):
    """
    Parses a log file to extract the first significant stack trace or error block.
    Supports Python, Java, JavaScript, and generic logs.
    """
    if not os.path.exists(log_path):
        print(f"[Error] Log file not found: {log_path}", file=sys.stderr)
        sys.exit(1)

    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    traceback_lines = []
    in_traceback = False
    
    # Simple regexes to find traces
    py_trace_start = re.compile(r"Traceback \(most recent call last\):")
    java_trace_line = re.compile(r"^\tat .*\(.*:\d+\)")
    generic_error = re.compile(r"(Exception|Error|Fail):", re.IGNORECASE)

    for i, line in enumerate(lines):
        # 1. Detect Python tracebacks
        if py_trace_start.search(line):
            in_traceback = True
            traceback_lines = lines[i:i+20]  # grab up to 20 lines
            break
        # 2. Detect Java tracebacks
        if java_trace_line.search(line):
            # Grab some context lines before and after
            start = max(0, i - 2)
            end = min(len(lines), i + 15)
            traceback_lines = lines[start:end]
            break
        # 3. Detect generic errors
        if generic_error.search(line):
            start = max(0, i - 1)
            end = min(len(lines), i + 8)
            traceback_lines = lines[start:end]
            break

    if not traceback_lines:
        # Default: return last 15 lines of log
        print("[Info] No active traceback patterns detected. Analyzing trailing log lines.", file=sys.stderr)
        traceback_lines = lines[-15:]

    return "".join(traceback_lines).strip()

def analyze_log_content(error_snippet):
    """
    Sends the parsed log snippet to the Gemini API to analyze the root cause
    and suggest a resolution. Falls back to offline heuristic analysis if no key exists.
    """
    print("--- Log Analyzer & Root Cause Analyst ---")
    print(f"\n[Extracted Log Context]\n{'-'*40}\n{error_snippet}\n{'-'*40}")

    prompt = f"""You are a professional Site Reliability Engineer.
Analyze the following log snippet, explain the root cause, and suggest a resolution:

Log Snippet:
{error_snippet}

Provide your analysis in the following format:
1. Root Cause Summary: (One sentence explaining why it crashed)
2. Offending Component/File: (Identify the file and line number if possible)
3. Suggested Action: (Step-by-step instructions to fix the issue)
"""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[Warning] GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Falling back to local heuristic analysis.", file=sys.stderr)
        print("-" * 50)
        
        # Local offline heuristic analysis
        if "NullPointerException" in error_snippet or "NoneType" in error_snippet:
            print("1. Root Cause Summary: Attempted to reference an attribute or property on a Null/None value.")
            print("2. Offending Component/File: Likely in the line containing the error (NoneType / NullPointerException).")
            print("3. Suggested Action:")
            print("   - Verify that the target object is properly instantiated before accessing its attributes.")
            print("   - Add a check: `if obj is not None:` or equivalent null guarding logic.")
        elif "Timeout" in error_snippet or "Time limit" in error_snippet:
            print("1. Root Cause Summary: The request exceeded the configured time limit threshold.")
            print("2. Offending Component/File: Downstream network call or API gateway hook.")
            print("3. Suggested Action:")
            print("   - Verify network latency and check downstream API availability.")
            print("   - Increase timeout limits or wrap the connection in a circuit-breaker retry loop.")
        else:
            print("1. Root Cause Summary: Unidentified system exception or runtime fault.")
            print("2. Offending Component/File: Unspecified.")
            print("3. Suggested Action:")
            print("   - Verify configurations and inspect system environment variables.")
            print("   - Run in debug mode to trace object states at crash time.")
        print("-" * 50)
        return

    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        print("\nQuerying Gemini API for Root Cause Analysis...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        candidates = data.get("candidates", [])
        if candidates:
            rca_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            print("\n" + "=" * 40)
            print("GEMINI ROOT CAUSE ANALYSIS REPORT:")
            print("=" * 40)
            print(rca_text.strip())
            print("=" * 40)
        else:
            print("[Error] Gemini API returned no candidates.", file=sys.stderr)
            
    except requests.exceptions.RequestException as e:
        print(f"[Error] Network call to Gemini API failed: {e}", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze tracebacks in log files using Gemini.")
    parser.add_argument("log_file", help="Path to the log file to parse.")
    args = parser.parse_args()

    snippet = extract_error_context(args.log_file)
    analyze_log_content(snippet)
