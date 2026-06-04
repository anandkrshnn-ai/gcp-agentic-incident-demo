# Engineering Blog: Building a Robust Git Churn & Complexity Analyzer

In modern software development, identifying the riskiest files in a repository is a common problem. High code churn combined with high structural complexity usually points to hotspots that are prone to bugs and require additional testing. 

This post details the design decisions, trade-offs, and statistical iterations behind `git_churn_analyzer.py`—a lightweight, dependency-free risk assessment tool designed for local developer pipelines.

---

## 1. The Pitfalls of Naive Risk Models

Most basic repository analyzers use a simple linear score, such as:
$$\text{Risk} = (\text{Normalized Churn} \times 0.4) + (\text{Normalized Commits} \times 0.6) + (\text{Complexity} \times 0.5)$$

While easy to implement, this approach breaks down in real-world scenarios due to three primary issues:

1. **Extreme Sensitivity to Outliers**: In a typical software project, a few files undergo massive refactoring (e.g., thousands of lines added/deleted in a single commit) while the majority of files have minor changes. A min-max normalization (`x / max_val`) compresses all other files' metrics to near-zero, hiding the relative risk differences between normal files.
2. **Heavy-Tailed Distributions**: Code churn and commit counts naturally follow a power-law distribution (Pareto/Zipf's law) rather than a symmetric Gaussian distribution. Standard linear scaling fails to capture the true shape of this data.
3. **Language Bias**: AST complexity analysis is typically language-specific. In a polyglot repository, files written in unsupported languages receive a baseline score of `0`, skewing the risk rankings.

---

## 2. The Solution: Log-MAD Robust Statistics

To address the distribution and outlier challenges, we redesigned the risk scoring framework to use robust statistical methods.

```
+------------------+     +--------------------+     +-------------------+
|  Raw Churn /     | --> | Log-Transformation | --> | Robust Z-Scores   |
|  Commits / Comp  |     |   y = ln(x + 1)    |     | using Median/MAD  |
+------------------+     +--------------------+     +-------------------+
                                                              |
                                                              v
+------------------+     +--------------------+     +-------------------+
| Risk Percentile  | <-- | Standardized Final | <-- | Weighted Composite|
|  via Normal CDF  |     |   Risk Z-Score     |     |    Risk Score     |
+------------------+     +--------------------+     +-------------------+
```

### Step 1: Log-Transformation
We first apply a log-transformation ($y = \ln(x + 1)$ or `math.log1p(x)`) to the raw counts of decayed churn, decayed commits, and complexity. This stabilizes the variance and compresses the heavy-tailed power-law distribution into a more symmetrical space.

### Step 2: Median and Median Absolute Deviation (MAD)
Instead of standard deviation, we calculate Z-scores using robust statistics:
- **Median** ($M$): The middle value of the log-transformed metrics, which is highly resistant to outliers.
- **Median Absolute Deviation** (MAD): The median of the absolute differences from the median:
  $$\text{MAD} = \text{median}(|y_i - M|)$$
- **Robust Standard Deviation**: We scale MAD by $1.4826$ to make it a consistent estimator of standard deviation under a standard normal distribution:
  $$\sigma_{\text{robust}} = 1.4826 \times \text{MAD}$$

The robust Z-score for a file is then computed as:
$$Z_{\text{robust}} = \frac{y_i - M}{\sigma_{\text{robust}}}$$

This approach ensures that a single 10,000-line change does not distort the standard deviation, preserving the visibility of risk in the rest of the files.

### Step 3: Composite Score and Normal CDF Percentile
After combining the robust Z-scores for churn, commits, and complexity using configurable weights, we standardize the resulting composite raw risk scores again to get a final standardized score $Z_{\text{final}}$.

Finally, we map $Z_{\text{final}}$ to a percentile using the standard normal Cumulative Distribution Function (CDF):
$$\text{Percentile} = \Phi(Z_{\text{final}}) = 0.5 \times \left(1 + \text{erf}\left(\frac{Z_{\text{final}}}{\sqrt{2}}\right)\right) \times 100$$

This gives the user an intuitive percentage ranking (e.g., *"This file is in the 98th percentile of risk relative to the rest of this repository"*).

---

## 3. Pluggable Complexity Architectures

To handle polyglot repositories without breaking, we implemented a simple **analyzer plugin registry**:

- **Python Analyzer (`.py`)**: Uses Python's native `ast` module to walk the Abstract Syntax Tree, counting conditional expressions (`If`, `IfExp`), loops (`For`, `While`), exception handlers (`ExceptHandler`), context managers (`With`), boolean operations (`BoolOp`), and comprehension filters.
- **Generic Fallback**: Scans text lines to heuristically count indentation block levels (4 spaces/1 tab increment = 1 complexity step) and basic control flow keywords (`if`, `for`, `while`, `catch`, etc.).
- **Extensibility**: Developers can register specialized AST analyzers for other file extensions (like `.js`, `.go`) directly into the `COMPLEXITY_REGISTRY` dictionary without modifying the core risk engine.

---

## 4. Key Engineering Trade-Offs

1. **`--no-renames` vs. Rename Tracking**: By default, the tool executes `git log` with the `--no-renames` flag. This avoids parsing errors caused by complex git rename formats (e.g. `src/{old_name => new_name}/module.py`), but it means renamed files lose their historical continuity and start with a reset decay calculation.
2. **In-Memory Buffering**: The command stdout is read as a single Python string. While this is fast and simple for small-to-medium repos, it creates an in-memory scale bottleneck for repositories with millions of commits.
3. **Synchronous Execution**: The tool processes files synchronously on a single CPU thread to keep the code clean and prevent dependency overhead (no multi-processing/multi-threading libraries required).
