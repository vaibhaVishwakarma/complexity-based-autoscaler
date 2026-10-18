---
name: docx-math-and-algorithms
description: "Format publication-quality mathematical notation, inline subscripts/superscripts, display equations (OMML), and IEEE/ACM-style academic algorithms in Word documents (.docx) using python-docx. Use whenever generating or modifying docx manuscripts containing scientific formulas, mathematical symbols (e.g., T_boot, D_SLA, q_hat, Greek letters), numbered equations, or pseudocode algorithms."
---

# DOCX Math & Algorithms Formatting Guide

This skill provides verified, schema-compliant methods for formatting academic mathematics and algorithms in `.docx` files using `python-docx` without relying on external GUI tools or unverified libraries.

---

## 1. Core Principles

1. **Typographic Integrity**:
   - Variables are rendered in *italics* (e.g., $T$, $D$, $k$, $\mu$).
   - Text subscripts are rendered in **Roman (upright)** text with `font.subscript = True` (e.g., $T_{\text{boot}}$, $D_{\text{SLA}}$, $k_{\text{reg}}$).
   - Numerical exponents are rendered with `font.superscript = True` (e.g., $10^{-44}$, $T^*$).
   - Greek letters and mathematical operators use standard Unicode symbols ($\alpha, \mu, \tau, \lambda, \Delta, \hat{q}, \le, \ge, \sum, \approx$).

2. **No Raw ASCII Approximations in Formal Text**:
   - Never write `T_boot` in formal report prose; format as $T_{\text{boot}}$ (`T` in italics, `boot` as subscript).
   - Never write `D_SLA`; format as $D_{\text{SLA}}$.
   - Never write `10^-44`; format as $10^{-44}$ (`-44` as superscript).
   - Never write `q_hat`; format as $\hat{q}$.
   - Never write `tau_down`; format as $\tau_{\text{down}}$.

3. **OpenXML Schema Compliance**:
   - Inline formatting uses standard OpenXML `<w:vertAlign w:val="subscript"/>` and `<w:vertAlign w:val="superscript"/>`.
   - Display equations use standard Office Math Markup Language (OMML) `<m:oMathPara>` and `<m:oMath>` within namespace `http://schemas.openxmlformats.org/officeDocument/2006/math`.
   - Academic algorithms use single-column tables with custom top/bottom thick borders (`w:sz="12"`) and internal caption border (`w:sz="6"`), ensuring 100% compatibility across Microsoft Word and LibreOffice.

---

## 2. Reusable Modular Utilities

Use the bundled module in `scripts/omml_builder.py`:

```python
from scripts.omml_builder import (
    add_formatted_math_text,
    add_omml_equation,
    add_academic_algorithm
)
```

### A. Inline Mathematical Notation
Instead of manually creating dozens of runs for mixed text and math:

```python
p = doc.add_paragraph()
add_formatted_math_text(
    p,
    "Under acute semantic complexity shocks, when container boot delay T_boot >= 15 s exceeds "
    "the latency deadline budget D_SLA = 15 s, statistical significance reached p = 2.07 x 10^-44."
)
```
This automatically parses:
- `T_boot` $\to$ italic $T$ + subscript $\text{boot}$
- `D_SLA` $\to$ italic $D$ + subscript $\text{SLA}$
- `10^-44` $\to$ base $10$ + superscript $-44$
- `q_hat` $\to$ $\hat{q}$
- `mu` $\to$ $\mu$
- `tau_down` $\to$ $\tau_{\text{down}}$

### B. Display Equations (OMML)
Insert centered display equations with optional right-aligned equation numbering:

```python
from docx.oxml import parse_xml

# RAPS Non-Conformity Score
raps_omml = '''
<m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
  <m:oMath>
    <m:sSub>
      <m:e><m:r><m:t>S</m:t></m:r></m:e>
      <m:sub><m:r><m:t>i</m:t></m:r></m:sub>
    </m:sSub>
    <m:r><m:t>(x, y) = </m:t></m:r>
    <m:nary>
      <m:naryPr><m:chr m:val="∑"/></m:naryPr>
      <m:sub><m:r><m:t>j=1</m:t></m:r></m:sub>
      <m:sup><m:r><m:t>k</m:t></m:r></m:sup>
      <m:e>
        <m:sSub>
          <m:e><m:r><m:t>π</m:t></m:r></m:e>
          <m:sub><m:r><m:t>j</m:t></m:r></m:sub>
        </m:sSub>
        <m:r><m:t>(x) + λ·max(0, k - </m:t></m:r>
        <m:sSub>
          <m:e><m:r><m:t>k</m:t></m:r></m:e>
          <m:sub><m:r><m:t>reg</m:t></m:r></m:sub>
        </m:sSub>
        <m:r><m:t>)</m:t></m:r>
      </m:e>
    </m:nary>
  </m:oMath>
</m:oMathPara>
'''
doc._body._body.append(parse_xml(raps_omml))
```

### C. Academic Algorithms (IEEE / ACM 3-Rule Environment)
Format formal algorithms with input/output blocks, line numbering, keyword highlighting, and indentation:

```python
steps = [
    (1, 0, "Initialize cooldown timer tau_down <- 0, boot lock T_lock <- 0, worker pool k <- 1"),
    (2, 0, "for each actuation epoch t = 1, 2, ... with interval Delta_t = 5 s do"),
    (3, 1, "Compute empirical offload derivative: Delta_offload(t) <- Offload(t) - Offload(t-1)"),
    (4, 1, "Sample cloud queue backlog L_q(t) and active worker pool k(t)"),
    (5, 1, "if Delta_offload(t) > 0 and T_lock == 0 then"),
    (6, 2, "Compute proactive target: k*(t) <- ceil( (L_q(t) + Delta_offload(t)) / mu )"),
    (7, 2, "Provision delta_k <- max(0, k*(t) - k(t)) cloud workers and set T_lock <- T_boot"),
    (8, 1, "else if L_q(t) == 0 and tau_down >= 30 s then"),
    (9, 2, "Scale down cautiously: k(t) <- max(k_min, k(t) - 1) and reset tau_down <- 0"),
    (10, 1, "end if"),
    (11, 0, "end for"),
    (12, 0, "return active cloud worker allocation trajectory k*(1:T)")
]

add_academic_algorithm(
    doc=doc,
    alg_num=1,
    title="Conformal-Gated Dual-Horizon Online Autoscaling (CGDA)",
    inputs="Arrival stream {x_i}, calibrated quantile threshold q_hat = 0.79914, service rate mu = 16.0 RPS, boot delay T_boot = 15 s",
    outputs="Elastic cloud worker allocation trajectory k*(t) over horizon T",
    lines=steps
)
```

---

## 3. Verification Protocol

After formatting mathematical documents:
1. Validate OpenXML schema compliance:
   `python .agents/skills/docx/scripts/office/validate.py output.docx`
2. Render to PDF via headless LibreOffice and inspect typography:
   `libreoffice --headless --convert-to pdf output.docx --outdir /tmp/`
   `pdftoppm -png -r 150 /tmp/output.pdf /tmp/page`
3. Verify that subscripts, superscripts, and Greek letters align precisely on their baselines without line height distortion.
