#!/usr/bin/env python3
"""
word-doc/scripts/omml_builder.py — Modular Mathematical Notation and Algorithm Builder for python-docx

Provides schema-compliant utilities for:
1. Parsing and rendering inline mathematical symbols, subscripts, superscripts, and Greek letters.
2. Injecting native OMML (Office Math Markup Language) display equations into python-docx documents.
3. Generating publication-grade academic algorithms with IEEE/ACM 3-rule styling.
"""

from __future__ import annotations

import re
from typing import List, Tuple, Optional
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

# Common mathematical replacements and token patterns
MATH_SUB_PATTERNS = [
    # (Regex pattern, Base text, Base italic, Sub/Sup text, Sub/Sup italic, is_sup)
    (r"\bT_boot\b", "T", True, "boot", False, False),
    (r"\bD_SLA\b", "D", True, "SLA", False, False),
    (r"\bT_lock\b", "T", True, "lock", False, False),
    (r"\bT_sim\b", "T", True, "sim", False, False),
    (r"\btau_down\b", "τ", False, "down", False, False),
    (r"\bt_down\b", "t", True, "down", False, False),
    (r"\blambda_edge\b", "λ", False, "edge", False, False),
    (r"\blambda_cloud\b", "λ", False, "cloud", False, False),
    (r"\blambda_slow\b", "λ", False, "slow", False, False),
    (r"\blambda_reg\b", "λ", False, "reg", False, False),
    (r"\btheta_shock\b", "θ", False, "shock", False, False),
    (r"\bdeltaK_t\b", "Δk", True, "t", True, False),
    (r"\bDelta_k_t\b", "Δk", True, "t", True, False),
    (r"\bp_fast\b", "p", True, "fast", False, False),
    (r"\bC_boot\b", "C", True, "boot", False, False),
    (r"\bt_last_scale\b", "t", True, "last_scale", False, False),
    (r"\bB_max\b", "B", True, "max", False, False),
    (r"\bB_t\b", "B", True, "t", True, False),
    (r"\bk_max_up\b", "k", True, "max_up", False, False),
    (r"\bk_max_down\b", "k", True, "max_down", False, False),
    (r"\bk_desired\b", "k", True, "desired", False, False),
    (r"\bk_current\b", "k", True, "current", False, False),
    (r"\bk_drain\b", "k", True, "drain", False, False),
    (r"\bk_proactive\b", "k", True, "proactive", False, False),
    (r"\bdelta_pre\b", "δ", False, "pre", False, False),
    (r"\bDelta_offload\b", "Δ", False, "offload", False, False),
    (r"\bDelta_t\b", "Δt", False, "", False, False),
    (r"\bDelta t\b", "Δt", False, "", False, False),
    (r"\bk\*(?=[^A-Za-z0-9]|$)", "k", True, "*", False, True),
    (r"\bT\*(?=[^A-Za-z0-9]|$)", "T", True, "*", False, True),
    (r"\bq_hat\b", "q*", True, "", False, False),
    (r"\bk_reg\b", "k", True, "reg", False, False),
    (r"\bL_q\b", "L", True, "q", True, False),
    (r"\bk_min\b", "k", True, "min", False, False),
    (r"\bk_max\b", "k", True, "max", False, False),
    (r"\bS_i\b", "S", True, "i", True, False),
    (r"\bx_i\b", "x", True, "i", True, False),
    (r"\bpi_j\b", "π", False, "j", True, False),
    (r"\bpi_k\b", "π", False, "k", True, False),
    (r"\blambda\b", "λ", False, "", False, False),
    (r"\bDelta\b", "Δ", False, "", False, False),
    (r"\bdelta\b", "δ", False, "", False, False),
    (r"\bbeta\b", "β", False, "", False, False),
    (r"\bgamma\b", "γ", False, "", False, False),
    (r"\btheta\b", "θ", False, "", False, False),
    (r"\balpha\b", "α", False, "", False, False),
    (r"\bmu\b", "μ", False, "", False, False),
    (r"\brho\b", "ρ", False, "", False, False),
    (r"\bsigma\b", "σ", False, "", False, False),
    (r"\btau\b", "τ", False, "", False, False),
    (r"\bepsilon\b", "ε", False, "", False, False),
    (r"\bapprox\b", "≈", False, "", False, False),
]

# Superscript pattern: e.g., 10^-44, 2^n, W^+, T^*
SUPERSCRIPT_REGEX = re.compile(r"(\b\d+|\b[A-Za-z])\^(-?\d+|[A-Za-z]|\+|\*)")

# General subscript pattern: e.g., X_i, W_q, W_{t+1}, W_(t+1)
GENERAL_SUB_REGEX = re.compile(r"\b([A-Za-z])_(?:\{([^}]+)\}|\(([^)]+)\)|([A-Za-z0-9]+))(?!\w)")


def add_formatted_math_text(
    paragraph: docx.text.paragraph.Paragraph,
    text: str,
    font_name: str = "Times New Roman",
    font_size_pt: float = 12.0,
    bold: bool = False,
    italic: bool = False,
) -> None:
    """
    Parses a string containing mathematical notations and appends properly formatted
    runs with italic variables, typographic subscripts, superscripts, and Greek symbols.
    """
    # Tokenize by mathematical patterns
    token_pattern = re.compile(
        r"(\bp_fast\^\(0\)|d\^2lambda/dt\^2|\(z\)\^\+|max\(0,\s*z\)|\bpi_hat_j\b|\bdot_p_fast\b|"
        r"\bT_boot\b|\bD_SLA\b|\bT_lock\b|\bT_sim\b|\btau_down\b|\bt_down\b|\blambda_edge\b|\blambda_cloud\b|\blambda_slow\b|"
        r"\blambda_reg\b|\btheta_shock\b|\bdeltaK_t\b|\bDelta_k_t\b|\bp_fast\b|\bC_boot\b|\bt_last_scale\b|\bB_max\b|\bB_t\b|"
        r"\bk_max_up\b|\bk_max_down\b|\bk_desired\b|\bk_current\b|\bk_drain\b|\bk_proactive\b|\bdelta_pre\b|"
        r"\bDelta_offload\b|\bDelta_t\b|\bDelta t\b|\bDelta\s+p\b|\bDelta\s+Q\b|\bq_hat\b|\bk_reg\b|\bL_q\b|\bk_min\b|\bk_max\b|\bS_i\b|\bx_i\b|"
        r"\bpi_j\b|\bpi_k\b|\blambda\b|\bDelta\b|\bdelta\b|\bbeta\b|\bgamma\b|\btheta\b|\balpha\b|\bmu\b|\brho\b|\bsigma\b|\btau\b|\bepsilon\b|\bapprox\b|"
        r"k\*(?=[^A-Za-z0-9]|$)|T\*(?=[^A-Za-z0-9]|$)|"
        r">>|<<|<=|>=|!=|->|<-|\s\*\s|\(t\)|\(t-1\)|\(t\+1\)|"
        r"\b\d+\^-?\d+|\b[A-Za-z]\^[A-Za-z0-9\+\*]+|\b[A-Za-z]_(?:\{[^}]+\}|\([^)]+\)|[A-Za-z0-9]+))"
    )

    tokens = token_pattern.split(text)

    for token in tokens:
        if not token:
            continue

        # Handle math dot multiplication
        if token == " * ":
            r = paragraph.add_run(" ⋅ ")
            r.font.name = font_name
            r.font.size = Pt(font_size_pt)
            r.font.bold = bold
            r.font.italic = False
            continue

        # Handle p_fast^(0)
        if token == "p_fast^(0)":
            r1 = paragraph.add_run("p")
            r1.font.name = font_name
            r1.font.size = Pt(font_size_pt)
            r1.font.bold = bold
            r1.font.italic = True

            r2 = paragraph.add_run("fast")
            r2.font.name = font_name
            r2.font.size = Pt(font_size_pt)
            r2.font.bold = bold
            r2.font.subscript = True

            r3 = paragraph.add_run("(0)")
            r3.font.name = font_name
            r3.font.size = Pt(font_size_pt)
            r3.font.bold = bold
            r3.font.superscript = True
            continue

        # Handle pi_hat_j
        if token == "pi_hat_j":
            r1 = paragraph.add_run("π̂")
            r1.font.name = font_name
            r1.font.size = Pt(font_size_pt)
            r1.font.bold = bold
            r1.font.italic = False

            r2 = paragraph.add_run("j")
            r2.font.name = font_name
            r2.font.size = Pt(font_size_pt)
            r2.font.bold = bold
            r2.font.italic = True
            r2.font.subscript = True
            continue

        # Handle d^2lambda/dt^2
        if token == "d^2lambda/dt^2":
            r1 = paragraph.add_run("d")
            r1.font.name = font_name
            r1.font.size = Pt(font_size_pt)
            r1.font.bold = bold
            r1.font.italic = True

            r2 = paragraph.add_run("2")
            r2.font.name = font_name
            r2.font.size = Pt(font_size_pt)
            r2.font.bold = bold
            r2.font.superscript = True

            r3 = paragraph.add_run("λ/dt")
            r3.font.name = font_name
            r3.font.size = Pt(font_size_pt)
            r3.font.bold = bold
            r3.font.italic = True

            r4 = paragraph.add_run("2")
            r4.font.name = font_name
            r4.font.size = Pt(font_size_pt)
            r4.font.bold = bold
            r4.font.superscript = True
            continue

        # Handle (z)^+
        if token == "(z)^+":
            r1 = paragraph.add_run("(")
            r1.font.name = font_name
            r1.font.size = Pt(font_size_pt)
            r1.font.bold = bold

            r2 = paragraph.add_run("z")
            r2.font.name = font_name
            r2.font.size = Pt(font_size_pt)
            r2.font.bold = bold
            r2.font.italic = True

            r3 = paragraph.add_run(")")
            r3.font.name = font_name
            r3.font.size = Pt(font_size_pt)
            r3.font.bold = bold

            r4 = paragraph.add_run("+")
            r4.font.name = font_name
            r4.font.size = Pt(font_size_pt)
            r4.font.bold = bold
            r4.font.superscript = True
            continue

        # Handle max(0, z)
        if re.fullmatch(r"max\(0,\s*z\)", token):
            r1 = paragraph.add_run("max(0, ")
            r1.font.name = font_name
            r1.font.size = Pt(font_size_pt)
            r1.font.bold = bold

            r2 = paragraph.add_run("z")
            r2.font.name = font_name
            r2.font.size = Pt(font_size_pt)
            r2.font.bold = bold
            r2.font.italic = True

            r3 = paragraph.add_run(")")
            r3.font.name = font_name
            r3.font.size = Pt(font_size_pt)
            r3.font.bold = bold
            continue

        # Handle dot_p_fast
        if token == "dot_p_fast":
            r1 = paragraph.add_run("ṗ")
            r1.font.name = font_name
            r1.font.size = Pt(font_size_pt)
            r1.font.bold = bold
            r1.font.italic = True

            r2 = paragraph.add_run("fast")
            r2.font.name = font_name
            r2.font.size = Pt(font_size_pt)
            r2.font.bold = bold
            r2.font.subscript = True
            continue

        # Handle time index functions like (t), (t-1), (t+1) with italic variable
        if token in ("(t)", "(t-1)", "(t+1)"):
            inner = token[1:-1]
            r_lp = paragraph.add_run("(")
            r_lp.font.name = font_name
            r_lp.font.size = Pt(font_size_pt)
            r_lp.font.bold = bold
            r_lp.font.italic = False

            r_in = paragraph.add_run(inner)
            r_in.font.name = font_name
            r_in.font.size = Pt(font_size_pt)
            r_in.font.bold = bold
            r_in.font.italic = True

            r_rp = paragraph.add_run(")")
            r_rp.font.name = font_name
            r_rp.font.size = Pt(font_size_pt)
            r_rp.font.bold = bold
            r_rp.font.italic = False
            continue

        # Handle Delta p and Delta Q
        if token.startswith("Delta ") or token == "Delta p" or token == "Delta Q":
            var_char = token.split()[1]
            r_delta = paragraph.add_run("Δ")
            r_delta.font.name = font_name
            r_delta.font.size = Pt(font_size_pt)
            r_delta.font.bold = bold
            r_delta.font.italic = False

            r_sp = paragraph.add_run(" ")
            r_sp.font.name = font_name
            r_sp.font.size = Pt(font_size_pt)
            r_sp.font.bold = bold

            r_var = paragraph.add_run(var_char)
            r_var.font.name = font_name
            r_var.font.size = Pt(font_size_pt)
            r_var.font.bold = bold
            r_var.font.italic = True
            continue

        # 1. Check known specific math patterns
        matched_specific = False
        for item in MATH_SUB_PATTERNS:
            pat = item[0]
            base = item[1]
            b_italic = item[2]
            sub = item[3]
            s_italic = item[4]
            is_sup = item[5] if len(item) > 5 else False

            if re.fullmatch(pat, token):
                r_base = paragraph.add_run(base)
                r_base.font.name = font_name
                r_base.font.size = Pt(font_size_pt)
                r_base.font.bold = bold
                r_base.font.italic = b_italic or italic

                if sub:
                    r_sub = paragraph.add_run(sub)
                    r_sub.font.name = font_name
                    r_sub.font.size = Pt(font_size_pt)
                    r_sub.font.bold = bold
                    r_sub.font.italic = s_italic
                    if is_sup:
                        r_sub.font.superscript = True
                    else:
                        r_sub.font.subscript = True
                matched_specific = True
                break

        if matched_specific:
            continue

        # 2. Check superscript pattern (e.g. 10^-44)
        m_sup = SUPERSCRIPT_REGEX.fullmatch(token)
        if m_sup:
            base, sup = m_sup.groups()
            r_base = paragraph.add_run(base)
            r_base.font.name = font_name
            r_base.font.size = Pt(font_size_pt)
            r_base.font.bold = bold
            r_base.font.italic = italic

            r_sup = paragraph.add_run(sup)
            r_sup.font.name = font_name
            r_sup.font.size = Pt(font_size_pt)
            r_sup.font.bold = bold
            r_sup.font.superscript = True
            continue

        # 3. Check general subscript pattern (e.g. W_q, W_(t+1), W_{t+1})
        m_sub = GENERAL_SUB_REGEX.fullmatch(token)
        if m_sub:
            base = m_sub.group(1)
            sub = m_sub.group(2) or m_sub.group(3) or m_sub.group(4)
            r_base = paragraph.add_run(base)
            r_base.font.name = font_name
            r_base.font.size = Pt(font_size_pt)
            r_base.font.bold = bold
            r_base.font.italic = True  # Math variables are italic

            r_sub = paragraph.add_run(sub)
            r_sub.font.name = font_name
            r_sub.font.size = Pt(font_size_pt)
            r_sub.font.bold = bold
            r_sub.font.italic = True  # Subscripts like t, t+1, i are italic
            r_sub.font.subscript = True
            continue

        # 4. Operators and Greek symbols
        symbol_map = {
            "<=": "≤",
            ">=": "≥",
            "!=": "≠",
            "->": "→",
            "<-": "←",
            ">>": "≫",
            "<<": "≪",
            "approx": "≈",
        }
        display_token = symbol_map.get(token, token)

        # Standard plain text run
        r = paragraph.add_run(display_token)
        r.font.name = font_name
        r.font.size = Pt(font_size_pt)
        r.font.bold = bold
        r.font.italic = italic


def add_omml_equation(
    doc: docx.Document,
    omml_xml: str,
    eq_number: Optional[str] = None,
) -> None:
    """
    Appends an OMML display equation to the document body.
    If eq_number is specified, formats the equation with a right-aligned number.
    """
    if eq_number:
        # 1-row, 2-col borderless table for equation and right-aligned number
        tbl = doc.add_table(rows=1, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        tbl.columns[0].width = Inches(4.85)
        tbl.columns[1].width = Inches(0.90)
        tbl.rows[0].cells[0].width = Inches(4.85)
        tbl.rows[0].cells[1].width = Inches(0.90)

        # Clean cell margins
        for cell in tbl.rows[0].cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tcBorders = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                '<w:top w:val="none"/>'
                '<w:left w:val="none"/>'
                '<w:bottom w:val="none"/>'
                '<w:right w:val="none"/>'
                '</w:tcBorders>'
            )
            tcPr.append(tcBorders)

        cell_eq = tbl.rows[0].cells[0]
        p_eq = cell_eq.paragraphs[0]
        p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_eq.paragraph_format.space_before = Pt(4)
        p_eq.paragraph_format.space_after = Pt(4)
        p_eq._p.append(parse_xml(omml_xml))

        cell_num = tbl.rows[0].cells[1]
        tcMar_num = parse_xml(
            f'<w:tcMar {nsdecls("w")}>'
            '<w:top w:w="40" w:type="dxa"/>'
            '<w:left w:w="0" w:type="dxa"/>'
            '<w:bottom w:w="40" w:type="dxa"/>'
            '<w:right w:w="0" w:type="dxa"/>'
            '</w:tcMar>'
        )
        cell_num._tc.get_or_add_tcPr().append(tcMar_num)
        p_num = cell_num.paragraphs[0]
        p_num.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_num.paragraph_format.space_before = Pt(4)
        p_num.paragraph_format.space_after = Pt(4)
        r_num = p_num.add_run(f"({eq_number})")
        r_num.font.name = "Times New Roman"
        r_num.font.size = Pt(12)
    else:
        # Standard centered display equation
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p._p.append(parse_xml(omml_xml))


def add_academic_algorithm(
    doc: docx.Document,
    alg_num: int,
    title: str,
    inputs: str,
    outputs: str,
    lines: List[Tuple[int, int, str]],
    width_in: float = 5.8,
) -> docx.table.Table:
    """
    Renders an IEEE/ACM-style 3-rule academic algorithm environment.
    
    Args:
        doc: The docx Document object.
        alg_num: Algorithm number (e.g. 1).
        title: Title string.
        inputs: Description of inputs.
        outputs: Description of outputs.
        lines: List of tuples (line_number, indent_level, pseudocode_text).
        width_in: Table width in inches.
    """
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.rows[0].cells[0].width = Inches(width_in)
    cell = tbl.rows[0].cells[0]

    # Apply 3-rule borders (top thick, bottom thick, no left/right)
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '<w:left w:val="none"/>'
        '<w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '<w:right w:val="none"/>'
        '</w:tcBorders>'
    )
    tcPr.append(tcBorders)

    # Title / Caption with separator border
    p_title = cell.paragraphs[0]
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(4)
    p_title.paragraph_format.line_spacing = 1.15
    pPr = p_title._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        '<w:bottom w:val="single" w:sz="6" w:space="4" w:color="000000"/>'
        '</w:pBdr>'
    )
    pPr.append(pBdr)

    r_num = p_title.add_run(f"Algorithm {alg_num}: ")
    r_num.font.name = "Times New Roman"
    r_num.font.size = Pt(11)
    r_num.font.bold = True
    r_tit = p_title.add_run(title)
    r_tit.font.name = "Times New Roman"
    r_tit.font.size = Pt(11)

    # Inputs & Outputs block
    p_io = cell.add_paragraph()
    p_io.paragraph_format.space_before = Pt(4)
    p_io.paragraph_format.space_after = Pt(4)
    p_io.paragraph_format.line_spacing = 1.15
    pPr_io = p_io._p.get_or_add_pPr()
    pBdr_io = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        '<w:bottom w:val="single" w:sz="4" w:space="4" w:color="CCCCCC"/>'
        '</w:pBdr>'
    )
    pPr_io.append(pBdr_io)

    r_in_l = p_io.add_run("Input: ")
    r_in_l.font.name = "Times New Roman"
    r_in_l.font.size = Pt(10)
    r_in_l.font.bold = True
    add_formatted_math_text(p_io, inputs + "\n", font_size_pt=10.0)

    r_out_l = p_io.add_run("Output: ")
    r_out_l.font.name = "Times New Roman"
    r_out_l.font.size = Pt(10)
    r_out_l.font.bold = True
    add_formatted_math_text(p_io, outputs, font_size_pt=10.0)

    # Pseudocode lines
    keywords = {"for", "each", "do", "if", "then", "else", "end", "while", "return", "repeat", "until"}

    for lno, indent_lvl, text in lines:
        p_step = cell.add_paragraph()
        p_step.paragraph_format.space_before = Pt(1)
        p_step.paragraph_format.space_after = Pt(1)
        p_step.paragraph_format.line_spacing = 1.1
        p_step.paragraph_format.left_indent = Inches(0.2 * indent_lvl)

        # Line number
        r_lno = p_step.add_run(f"{lno:2d}:  ")
        r_lno.font.name = "Courier New"
        r_lno.font.size = Pt(9.5)
        r_lno.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

        # Split words for keyword bolding vs math text
        words = text.split(" ")
        for w in words:
            if w in keywords:
                r_w = p_step.add_run(w + " ")
                r_w.font.name = "Times New Roman"
                r_w.font.size = Pt(10)
                r_w.font.bold = True
            else:
                add_formatted_math_text(p_step, w + " ", font_size_pt=10.0)

    # Spacing paragraph after table
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(4)
    p_after.paragraph_format.space_after = Pt(6)

    return tbl


def apply_table_grid_borders(table: docx.table.Table, color: str = "000000", sz: str = "4") -> None:
    """
    Applies a uniform solid grid border around every cell of a table (Option 1: full grid)
    using the official BCE497J template border specification:
    <w:tblBorders>
      <w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>
      <w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>
      <w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>
      <w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>
      <w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>
      <w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>
    </w:tblBorders>
    Also removes any overriding cell-level tcBorders to ensure clean and uniform rendering.
    """
    tblPr = table._tbl.tblPr
    existing_borders = tblPr.find(qn("w:tblBorders"))
    if existing_borders is not None:
        tblPr.remove(existing_borders)

    borders_xml = (
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(parse_xml(borders_xml))

    # Clear cell-level borders that could override table-level gridlines
    for row in table.rows:
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            existing_tc_borders = tcPr.find(qn("w:tcBorders"))
            if existing_tc_borders is not None:
                tcPr.remove(existing_tc_borders)

