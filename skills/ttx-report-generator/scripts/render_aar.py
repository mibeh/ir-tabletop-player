"""Render a TTX After-Action Report / Improvement Plan findings JSON to DOCX.

Usage:
    uv run python skills/ttx-report-generator/scripts/render_aar.py FINDINGS.json \
        [--output-dir DIR]

The document follows CISA's CTEP AAR/IP structure with a neutral visual style,
omitting the template's Core Capabilities reference and alternate-template
appendices.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Final

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

SLATE = "253746"
ORANGE = "FF5500"
_DEFAULT_SPONSOR = "IR Team"
_CLASSIFICATION = "TLP:AMBER+STRICT - CONFIDENTIAL"


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return slug[:60]


def _shade_cell(cell, fill_hex: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)


def _white_bold(cell) -> None:
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)


def _apply_header_row(cells, labels) -> None:
    """Fill a table's header cells with labels and apply the slate/white style."""
    for cell, label in zip(cells, labels):
        cell.text = label
        _shade_cell(cell, SLATE)
        _white_bold(cell)


def _autofit_contents(table) -> None:
    """Set *table* to Word's "AutoFit Contents" layout (columns sized to content).

    Mirrors the Table Layout > AutoFit > "AutoFit Contents" command: an autofit
    layout algorithm plus an ``auto`` preferred table width so Word sizes each
    column to its contents rather than to a fixed width.
    """
    tbl_pr = table._tbl.tblPr
    tbl_pr.get_or_add_tblLayout().set(qn("w:type"), "autofit")
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.insert_element_before(
            tbl_w,
            "w:jc",
            "w:tblCellSpacing",
            "w:tblInd",
            "w:tblBorders",
            "w:shd",
            "w:tblLayout",
            "w:tblCellMar",
            "w:tblLook",
            "w:tblCaption",
            "w:tblDescription",
        )
    tbl_w.set(qn("w:type"), "auto")
    tbl_w.set(qn("w:w"), "0")


def _set_base_style(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Lato"
    normal.font.size = Pt(10)


def _add_label_value_row(table, label: str, value: str) -> None:
    """Append a shaded-label / plain-value row to *table*.

    Args:
        table: The python-docx Table to append to.
        label: Text for the left (shaded) cell.
        value: Text for the right (plain) cell.
    """
    cells = table.add_row().cells
    cells[0].text = label
    cells[1].text = value
    _shade_cell(cells[0], SLATE)
    _white_bold(cells[0])


def build_overview_table(doc: Document, ov: dict) -> None:
    """Render the Exercise Overview two-column table into *doc*.

    Args:
        doc: The Document being built.
        ov: The ``exercise_overview`` dict from the findings JSON.
    """
    _heading(doc, "EXERCISE OVERVIEW", 16, SLATE)

    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    _autofit_contents(table)

    modules = ov.get("modules", [])
    module_titles = ", ".join(m.get("title") for m in modules if m.get("title"))
    scenario = ov.get("scenario_description", "")
    if modules:
        prefix = f"{scenario} " if scenario else ""
        scenario = (
            f"{prefix}The scenario consists of {len(modules)} module(s): "
            f"{module_titles}."
        )
    objectives = "\n".join(
        f"{i}. {obj}" for i, obj in enumerate(ov.get("objectives", []), start=1)
    )

    rows = [
        ("Exercise Name", ov.get("name", "")),
        ("Exercise Dates", ov.get("dates", "")),
        ("Scope", ov.get("scope", "")),
        ("Mission Area(s)", ", ".join(ov.get("mission_areas", []))),
        ("Core Capabilities", ", ".join(ov.get("core_capabilities", []))),
        ("Objectives", objectives),
        ("Threat or Hazard", ov.get("threat_or_hazard", "")),
        ("Scenario", scenario),
        ("Sponsor", ov.get("sponsor", "")),
        ("Participating Organizations", ov.get("participating_organizations", "")),
        ("Points of Contact", ov.get("points_of_contact", "")),
    ]
    for label, value in rows:
        _add_label_value_row(table, label, value)


def build_executive_summary(doc: Document, findings: dict) -> None:
    """Render the Executive Summary narrative section into *doc*.

    The summary is a free-text narrative authored in the findings JSON that
    frames the exercise objectives and highlights the most important strengths
    and areas for improvement. Blank lines separate paragraphs.

    Args:
        doc: The Document being built.
        findings: Full findings dict (produced by the TTX report generator).
    """
    _heading(doc, "EXECUTIVE SUMMARY", 16, SLATE)
    summary = (findings.get("executive_summary") or "").strip()
    if not summary:
        doc.add_paragraph("No executive summary was provided for this exercise.")
        return
    for paragraph in summary.split("\n"):
        paragraph = paragraph.strip()
        if paragraph:
            doc.add_paragraph(paragraph)


def build_title_page(doc: Document, ov: dict) -> None:
    """Add the title page paragraphs to *doc*.

    Args:
        doc: The Document being built.
        ov: The ``exercise_overview`` dict from the findings JSON.
    """
    doc.add_paragraph()
    name = doc.add_paragraph()
    name_run = name.add_run(ov.get("name", "Tabletop Exercise"))
    name_run.font.size = Pt(28)
    name_run.font.bold = True
    name_run.font.color.rgb = RGBColor.from_string(SLATE)

    subtitle = doc.add_paragraph()
    sub_run = subtitle.add_run(
        "Incident Response Tabletop Exercise — After-Action Report / Improvement Plan"
    )
    sub_run.font.size = Pt(18)
    sub_run.font.bold = True
    sub_run.font.color.rgb = RGBColor.from_string(ORANGE)

    doc.add_paragraph(ov.get("dates", ""))


def _heading(doc: Document, text: str, size: int, color: str) -> None:
    """Add a bold, coloured heading paragraph to *doc*.

    Args:
        doc: The Document being built.
        text: Heading text content.
        size: Font size in points.
        color: Hex colour string (no leading ``#``).
    """
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.bold = True
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)


def _labelled(doc: Document, label: str, value: str) -> None:
    """Add a bold-label followed by plain-value paragraph to *doc*.

    Args:
        doc: The Document being built.
        label: Bold label text (a colon and space are appended automatically).
        value: Plain-text value following the label.
    """
    para = doc.add_paragraph()
    label_run = para.add_run(f"{label}: ")
    label_run.font.bold = True
    label_run.font.color.rgb = RGBColor.from_string(SLATE)
    para.add_run(value)


def build_objective_analysis(doc: Document, findings: dict) -> None:
    """Render the Analysis of Exercise Objectives section into *doc*.

    Adds the section heading, intro paragraph, objective-capability alignment
    table, and one subsection per objective containing Strengths and Areas for
    Improvement observations.

    Args:
        doc: The Document being built.
        findings: Full findings dict (produced by the TTX report generator).
    """
    _heading(doc, "ANALYSIS OF EXERCISE OBJECTIVES", 16, SLATE)
    doc.add_paragraph(
        "The following section reviews performance against each exercise "
        "objective and its associated core capability, highlighting strengths "
        "and areas for improvement."
    )

    alignment = findings.get("objective_capability_alignment", [])
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    _autofit_contents(table)
    _apply_header_row(table.rows[0].cells, ["Objective", "Core Capability"])
    for entry in alignment:
        cells = table.add_row().cells
        cells[0].text = entry.get("objective", "")
        cells[1].text = ", ".join(entry.get("core_capabilities", []))

    for analysis in findings.get("objective_analyses", []):
        doc.add_paragraph()
        _heading(
            doc,
            f"Objective {analysis.get('number', '')}: {analysis.get('objective', '')}",
            14,
            SLATE,
        )
        _labelled(
            doc,
            "Core Capabilities",
            ", ".join(analysis.get("core_capabilities", [])),
        )

        _heading(doc, "Strengths", 12, ORANGE)
        strengths = analysis.get("strengths", [])
        if strengths:
            for strength in strengths:
                doc.add_paragraph(strength, style="List Bullet")
        else:
            doc.add_paragraph("No major strengths recorded for this objective.")

        _heading(doc, "Areas for Improvement", 12, ORANGE)
        afis = analysis.get("areas_for_improvement", [])
        if not afis:
            doc.add_paragraph("No areas for improvement recorded for this objective.")
        for index, afi in enumerate(afis, start=1):
            _labelled(doc, f"Area for Improvement {index}", afi.get("observation", ""))
            _labelled(doc, "Priority", afi.get("priority") or "Not Specified")
            references = afi.get("references", [])
            _labelled(
                doc,
                "Reference",
                "; ".join(references) if references else "Not Applicable",
            )
            _labelled(doc, "Analysis", afi.get("analysis", ""))
            _labelled(doc, "Recommendation", afi.get("recommendation", ""))


_IP_COLUMNS: Final = (
    "Exercise Objective",
    "Core Capability",
    "Issue/Area for Improvement",
    "Priority",
    "Corrective Action",
    "Capability Element",
    "Primary Responsible Organization",
    "Organization POC",
    "Start Date",
    "Completion Date",
)


def build_improvement_plan(doc: Document, findings: dict) -> None:
    """Render Appendix A: Improvement Plan matrix into *doc*.

    Adds the appendix heading, an introductory paragraph, and a 9-column
    CTEP-aligned table with one row per improvement plan entry.

    Args:
        doc: The Document being built.
        findings: Full findings dict (produced by the TTX report generator).
    """
    ov = findings.get("exercise_overview", {})
    _heading(doc, "APPENDIX A: IMPROVEMENT PLAN", 16, SLATE)
    doc.add_paragraph(
        f"This Improvement Plan was developed for {ov.get('sponsor') or _DEFAULT_SPONSOR} as a "
        f"result of {ov.get('name', '')} conducted on {ov.get('dates', '')}. "
        "Capability Elements are: Planning, Organization, Equipment, Training, "
        "or Exercise."
    )

    table = doc.add_table(rows=1, cols=len(_IP_COLUMNS))
    table.style = "Table Grid"
    _autofit_contents(table)
    _apply_header_row(table.rows[0].cells, _IP_COLUMNS)

    for row in findings.get("improvement_plan", []):
        cells = table.add_row().cells
        cells[0].text = row.get("exercise_objective", "")
        cells[1].text = row.get("core_capability", "")
        cells[2].text = row.get("issue", "")
        cells[3].text = row.get("priority") or "Not Specified"
        cells[4].text = "\n".join(row.get("corrective_actions", []))
        cells[5].text = row.get("capability_element", "")
        cells[6].text = row.get("responsible_organization", "")
        cells[7].text = row.get("poc", "")
        cells[8].text = row.get("start_date", "")
        cells[9].text = row.get("completion_date", "")


def build_participants(doc: Document, findings: dict) -> None:
    """Render Appendix B: the exercise participants roster table."""
    _heading(doc, "APPENDIX B: EXERCISE PARTICIPANTS", 16, SLATE)
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    _autofit_contents(table)
    _apply_header_row(
        table.rows[0].cells, ["Name", "Position", "Exercise Role", "Department"]
    )
    for person in findings.get("participants", []):
        cells = table.add_row().cells
        cells[0].text = person.get("name", "")
        cells[1].text = person.get("position", "")
        cells[2].text = person.get("exercise_role", "")
        cells[3].text = person.get("department", "")


def _start_section(doc: Document, orientation: WD_ORIENT) -> None:
    """Begin a new page-break section in *orientation*, swapping page dims to match."""
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    section.orientation = orientation
    width, height = section.page_width, section.page_height
    wants_landscape = orientation == WD_ORIENT.LANDSCAPE
    if wants_landscape == (width < height):
        section.page_width, section.page_height = height, width


def _configure_header_footer(doc: Document) -> None:
    """Set the running header and footer to the classification marking."""
    section = doc.sections[0]
    section.header.paragraphs[0].text = _CLASSIFICATION
    section.footer.paragraphs[0].text = _CLASSIFICATION


def render_aar(findings: dict, output_dir: Path) -> Path:
    """Render *findings* to a CTEP AAR/IP DOCX file.

    Args:
        findings: Parsed findings JSON dict (produced by the TTX report generator).
        output_dir: Directory to write the ``.docx`` into (created if absent).
    Returns:
        Path to the written ``.docx`` file (inside ``output_dir``).
    """
    ov = findings.get("exercise_overview", {})
    doc = Document()
    _set_base_style(doc)
    build_title_page(doc, ov)
    doc.add_page_break()
    build_overview_table(doc, ov)
    doc.add_page_break()
    build_executive_summary(doc, findings)
    doc.add_page_break()
    build_objective_analysis(doc, findings)
    _start_section(doc, WD_ORIENT.LANDSCAPE)
    build_improvement_plan(doc, findings)
    _start_section(doc, WD_ORIENT.PORTRAIT)
    build_participants(doc, findings)
    _configure_header_footer(doc)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(ov.get("name", "")) or "exercise"
    stamp = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_path = output_dir / f"aar-{slug}-{stamp}.docx"
    doc.save(str(out_path))
    return out_path


def main() -> None:
    """Entry point for the CLI renderer."""
    parser = argparse.ArgumentParser(description="Render a TTX AAR/IP findings JSON to DOCX.")
    parser.add_argument("findings", type=Path, help="Path to the findings JSON file.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "reports",
        help="Directory to write the .docx into (default: the skill's reports/).",
    )
    args = parser.parse_args()
    findings = json.loads(args.findings.read_text(encoding="utf-8"))
    out_path = render_aar(findings, args.output_dir)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
