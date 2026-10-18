#!/usr/bin/env python3
"""
scripts/omml_builder.py — Modular Mathematical Notation and Algorithm Builder for python-docx

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
from docx.oxml.ns import nsdecls

# Common mathematical replacements and token patterns
MATH_SUB_PATTERNS = [
    # (Regex pattern, Base text, Base italic, Subscript text, Subscript italic)
    (r"\bT_boot\b", "T", True, "boot", False),
    (r"\bD_SLA\b", "D", True, "SLA", False),
    (r"\bT_lock\b", "T", True, "lock", False),
    (r"\btau_down\b", "τ", False, "down", False),
    (r"\bDelta_offload\b", "Δ", False, "offload", False),
    (r"\bDelta_t\b", "Δt", False, "", False),
    (r"\bq_hat\b", "q̂", False, "", False),
    (r"\bk_reg\b", "k", True, "reg", False),
    (r"\blambda_reg\b", "λ", False, "reg", False),
    (r"\bL_q\b", "L", True, "q", True),
    (r"\bk_min\b", "k", True, "min", False),
    (r"\bk_max\b", "k", True, "max", False),
    (r"\bS_i\b", "S", True, "i", True),
    (r"\bx_i\b", "x", True, "i", True),
    (r"\bpi_j\b", "π", False, "j", True),
    (r"\bpi_k\b", "π", False, "k", True),
    (r"\bT\*\b", "T*", True, "", False),
]

# Superscript pattern: e.g., 10^-44, 2^n
SUPERSCRIPT_REGEX = re.compile(r"(\b\d+|\b[A-Za-z])\^(-?\d+|[A-Za-z])")

# General subscript pattern: e.g., X_i, W_q
GENERAL_SUB_REGEX = re.compile(r"\b([A-Za-z])_([A-Za-z0-9]+)\b")


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
    # Master pattern combines known math terms, superscripts, and general subscripts
    token_pattern = re.compile(
        r"(\bT_boot\b|\bD_SLA\b|\bT_lock\b|\btau_down\b|\bDelta_offload\b|\bDelta_t\b|"
        r"\bq_hat\b|\bk_reg\b|\blambda_reg\b|\bL_q\b|\bk_min\b|\bk_max\b|\bS_i\b|\bx_i\b|"
        r"\bpi_j\b|\bpi_k\b|\bT\*\b|\b\d+\^-?\d+|\b[A-Za-z]\^[A-Za-z0-9]+|\b[A-Za-z]_[A-Za-z0-9]+|<=|>=|!=|->|<-)"
    )

    tokens = token_pattern.split(text)

    for token in tokens:
        if not token:
            continue

        # 1. Check known specific math patterns
        matched_specific = False
        for pat, base, b_italic, sub, s_italic in MATH_SUB_PATTERNS:
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

        # 3. Check general subscript pattern (e.g. W_q)
        m_sub = GENERAL_SUB_REGEX.fullmatch(token)
        if m_sub:
            base, sub = m_sub.groups()
            r_base = paragraph.add_run(base)
            r_base.font.name = font_name
            r_base.font.size = Pt(font_size_pt)
            r_base.font.bold = bold
            r_base.font.italic = True  # Math variables are italic

            r_sub = paragraph.add_run(sub)
            r_sub.font.name = font_name
            r_sub.font.size = Pt(font_size_pt)
            r_sub.font.bold = bold
            r_sub.font.italic = (len(sub) == 1)  # Single letter subscript is italic
            r_sub.font.subscript = True
            continue

        # 4. Operators and Greek symbols
        symbol_map = {
            "<=": "≤",
            ">=": "≥",
            "!=": "≠",
            "->": "→",
            "<-": "←",
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
        tbl.rows[0].cells[0].width = Inches(5.2)
        tbl.rows[0].cells[1].width = Inches(0.8)

        # Clean cell margins
        for cell in tbl.rows[0].cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tcBorders = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                '<w:top w:val="none"/>'
                '<w:bottom w:val="none"/>'
                '<w:left w:val="none"/>'
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
        '<w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '<w:left w:val="none"/>'
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
