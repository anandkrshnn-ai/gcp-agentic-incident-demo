# Technical Reference: Git Churn & Complexity Analyzer

This document explains the statistical modeling, default weight parameters, and architecture decisions of the `git_churn_analyzer.py` tool.

---

## 1. Statistical Risk Modeling

Software changes do not follow a Gaussian (normal) distribution. Instead, repository metrics like lines churned and commit frequency follow heavy-tailed power-law distributions: a tiny subset of files absorbs the vast majority of modifications.

Standard Z-scoring and linear scaling fail under these conditions:
- **Linear normalizations** (e.g. `x / max`) are highly sensitive to outliers. If one vendor file undergoes a 20,000-line change, it compresses all other files' metrics toward `0.0`.
- **Standard Z-scores** use the mean and standard deviation, both of which are severely distorted by massive refactoring commits.

### The Log-MAD Pipeline

To construct an outlier-resistant risk metric, the analyzer processes raw counts through the following statistical pipeline:

1. **Log-Transformation**: We apply $y = \ln(x + 1)$ to raw code churn, commit frequency, and AST complexity. This stabilizes variance and compresses the heavy-tailed power-law distribution.
2. **Median Absolute Deviation (MAD)**: Rather than calculating variance from the mean, we calculate deviations from the median, which is highly resistant to outliers:
   $$\text{MAD} = \text{median}(|y_i - \text{median}(y)|)$$
3. **Robust Standard Deviation**: We scale MAD by a constant factor ($1.4826$) to estimate standard deviation under standard normal assumptions:
   $$\sigma_{\text{robust}} = 1.4826 \times \text{MAD}$$
4. **Robust Z-Score**:
   $$Z_{\text{robust}} = \frac{y_i - \text{median}(y)}{\sigma_{\text{robust}}}$$
5. **CDF Percentile Mapping**: We standardize the composite weighted scores of these metrics and map the final score to a percentile using the standard normal Cumulative Distribution Function (CDF) to provide a relative ranking from 0% to 100%.

---

## 2. Evidence-Based Weight Configuration

The tool weights raw Z-scores with the following default weights, derived from empirical software engineering research on defect prediction (e.g., *Nagappan et al.*, *Rahman & Devanbu*):

- **Code Churn (50% / `0.5`)**: Empirical studies demonstrate that the total volume of changed lines (decayed churn) is the strongest single statistical predictor of file defects, explaining approximately half of the post-release defect variance.
- **Commit Frequency (30% / `0.3`)**: The number of revisions indicates context-switching overhead and integration frequency. High commit touchpoints correlate with high developer friction and defect density.
- **AST Complexity (20% / `0.2`)**: While structural complexity (measured via AST branching points) indicates code that is harder to comprehend and modify, it often correlates with churn. Thus, it is weighted lower to prevent redundant signal overlap.

---

## 3. Simplified Architecture Trade-Offs

- **No Multi-Language Complexity Registry**: To avoid over-engineering, the analyzer only implements a native Python AST complexity parser. Files of other languages (YAML, HCL, JavaScript) bypass complexity calculations and receive a structural complexity of `0`.
- **Rename Disconnection**: The underlying `git log` command uses `--no-renames` to prevent path-parsing errors when handling complex rename syntaxes (e.g. `src/{a => b}/file.py`). The trade-off is that renamed files lose their historical continuity and decay statistics are reset.
- **Single-Threaded and In-Memory**: The tool parses raw `git log` output inside memory rather than utilizing stream readers or multi-threading, keeping the codebase small and free of external dependencies, but bounding scalability in very large repositories.
