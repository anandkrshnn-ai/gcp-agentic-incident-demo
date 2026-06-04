import os
import sys
import json
import argparse
import requests

def generate_test_code(feature_description, language="playwright"):
    """
    Sends a structured prompt to the Gemini API using direct HTTP requests
    to generate valid, runnable pytest or Playwright verification code.
    """
    print("--- AI Verification Script Generator ---")
    print(f"Feature Description: {feature_description}")
    print(f"Target Language: {language}")

    prompt = f"""You are a professional software verification engineer.
Generate a valid, clean, and runnable verification script for the following feature:
"{feature_description}"

Target Framework/Language: {language}

Requirements:
1. Output ONLY valid executable code. Do not include markdown code block styling (like ```python or ```) in your response.
2. Include comments explaining key verification assertions.
3. Handle basic setup and teardown within the script.
4. If testing APIs or web pages, use standard mock URLs or placeholders (e.g., https://httpbin.org/get or similar public sandboxes).
"""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[Warning] GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Falling back to a local dry-run (simulated output).", file=sys.stderr)
        print("-" * 50)
        print("Proposed Prompt:")
        print(prompt.strip())
        print("-" * 50)
        
        # Local mock fallback
        if language.lower() == "playwright":
            return f"""# Simulated Playwright test for: {feature_description}
import re
from playwright.sync_api import Page, expect

def test_verify_feature(page: Page):
    # Go to app dashboard or main page
    page.goto("https://httpbin.org/")
    
    # Verify page state
    expect(page).to_have_title(re.compile("httpbin"))
"""
        else:
            return f"""# Simulated pytest validation for: {feature_description}
import pytest

def test_verify_feature():
    data = {{"status": "success", "feature": "{feature_description}"}}
    assert data["status"] == "success"
    assert "{feature_description}" in data["feature"]
"""

    # Hit the Google AI Studio Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        print("\nSending request to Gemini API...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract generated content
        candidates = data.get("candidates", [])
        if candidates:
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            # Clean markdown formatting if returned
            text = text.replace("```python", "").replace("```javascript", "").replace("```typescript", "").replace("```", "").strip()
            return text
        else:
            print("[Error] Gemini API returned no candidates.", file=sys.stderr)
            sys.exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"[Error] Network call to Gemini API failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate automated verification scripts using Gemini.")
    parser.add_argument("--feature", required=True, help="Feature description in natural language.")
    parser.add_argument("--lang", default="playwright", help="Target framework (playwright, pytest).")
    parser.add_argument("--output", help="Save the generated code to a file path.")

    args = parser.parse_args()
    code = generate_test_code(args.feature, args.lang)
    
    print("\n" + "=" * 40)
    print("GENERATED VERIFICATION SCRIPT:")
    print("=" * 40)
    print(code)
    print("=" * 40)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"\nSaved generated script to: {args.output}")
