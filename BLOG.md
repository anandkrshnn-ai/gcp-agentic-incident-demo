# Git Churn & Complexity Analyzer: Technical Specifications

This document defines the mathematical modeling, default parameters, and design trade-offs of the `git_churn_analyzer.py` script.

---

## 1. Mathematical Scoring Model

The risk analyzer maps highly skewed, power-law distributed codebase metrics (code churn, commit count, AST complexity) to an outlier-resistant percentile ranking.

### Log-MAD Transformation Pipeline

For each file $i$ and metric $x$, the raw values are transformed as follows:

1. **Log-Transformation**:
   $$y_i = \ln(x_i + 1)$$
   *Rationale: Compresses heavy-tailed power-law distributions.*

2. **Median Absolute Deviation (MAD)**:
   $$\text{MAD} = \text{median}(|y_i - \text{median}(y)|)$$
   *Rationale: Provides a robust measure of statistical dispersion resistant to outliers.*

3. **Robust Standard Deviation**:
   $$\sigma = 1.4826 \times \text{MAD}$$
   *Rationale: Standard normal scale estimator.*

4. **Robust Z-Score**:
   $$Z_i = \frac{y_i - \text{median}(y)}{\sigma}$$

### Composite Risk & Standardized CDF Normalization

The composite raw risk score $R_i$ is computed as:
$$R_i = w_{\text{churn}} Z_{\text{churn}, i} + w_{\text{commits}} Z_{\text{commits}, i} + w_{\text{complexity}} Z_{\text{complexity}, i}$$

The composite raw scores are standardized to the final risk Z-score $Z_{\text{final}, i}$:
$$Z_{\text{final}, i} = \frac{R_i - \text{median}(R)}{\sigma_R}$$
*(Where $\sigma_R = 1.4826 \times \text{MAD}(R)$)*

Finally, the risk percentile $P_i$ is calculated using the normal Cumulative Distribution Function (CDF):
$$P_i = \Phi(Z_{\text{final}, i}) \times 100$$
$$\Phi(z) = \frac{1}{2} \left[1 + \text{erf}\left(\frac{z}{\sqrt{2}}\right)\right]$$

---

## 2. Sensitivity Analysis

The sensitivity of the final risk percentile $P_i$ to changes in raw metric values (e.g. churn $x$) is defined by the partial derivative:

$$\frac{\partial P}{\partial x} = 100 \cdot \phi(Z_{\text{final}}) \cdot \frac{1}{\sigma_R} \cdot w \cdot \frac{1}{\sigma_{\text{metric}} (x + 1)}$$

Where:
- $\phi(z) = \frac{1}{\sqrt{2\pi}} e^{-z^2/2}$ is the Standard Normal Probability Density Function (PDF).
- $\sigma_R$ is the robust composite standard deviation of the repository.
- $w$ is the metric weight (churn: 0.5, commits: 0.3, complexity: 0.2).
- $\sigma_{\text{metric}}$ is the robust standard deviation of the log-transformed metric across the repository.

### Key Sensitivity Observations
1. **Impact of Log-Scaling**: Because of the $\frac{1}{x+1}$ term, changes at low metric values (e.g., changing churn from 1 to 10 lines) produce larger shifts in risk percentile than identical absolute changes at high values (e.g., changing churn from 1,000 to 1,009 lines).
2. **Impact of Weight Coefficients**: With $w_{\text{churn}} = 0.5$, a change in churn Z-score has 2.5 times the sensitivity of a change in AST complexity Z-score ($w_{\text{complexity}} = 0.2$).
3. **Repository Scale Dependency**: Sensitivity scales inversely with the repository dispersion metrics $\sigma_R$ and $\sigma_{\text{metric}}$. In a uniform repository (small standard deviations), small metric updates cause rapid shifts in relative percentile ranking. In highly dispersed repositories (large standard deviations), percentiles remain stable against small updates.

---

## 3. Reference Weights Justification

- **Code Churn ($w_{\text{churn}} = 0.5$)**: Backed by empirical software engineering research (Nagappan et al., Rahman & Devanbu) pointing to the volume of churned lines as the single strongest statistical predictor of defects.
- **Commit Frequency ($w_{\text{commits}} = 0.3$)**: Reflects developer context switching and revision frequency.
- **AST Complexity ($w_{\text{complexity}} = 0.2$)**: Represents structural density (branching constructs) and acts as an secondary modifier.

---

## 4. Known Architectural Trade-Offs

- **AST Limit**: Only parses Python files; other extension profiles bypass analysis and return a default complexity of `0`.
- **Rename Boundary**: Uses `--no-renames` during history collection to prevent parser failures. Renamed files reset decay tracking.
- **Single-Threaded RAM Buffer**: Reads complete `git log --numstat` output into a contiguous string.
