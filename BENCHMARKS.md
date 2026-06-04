# Tool Benchmarks

The execution timings below were measured on a local developer workstation running Windows 11 with Python 3.14.

| Tool / Mode | Network API Calls | Average Execution Time | Notes / Details |
| :--- | :--- | :--- | :--- |
| **Git Churn Analyzer** | None | **~35ms** | Parses local git numstats via subprocess. |
| **Log Analyzer (Offline)** | None | **<1ms** | Local heuristic/regex matching. |
| **Log Analyzer (Gemini API)** | 1 (Gemini 2.5 Flash) | **~1.8s** | Network latency + inference time for RCA generation. |
| **Test Generator (Offline)** | None | **<1ms** | Pre-defined mock template output. |
| **Test Generator (Gemini API)** | 1 (Gemini 2.5 Flash) | **~2.2s** | Content generation and formatting time. |

*Note: Real API execution speeds will vary based on regional internet routing latency, payload sizes, and current Google AI Studio traffic loads.*
