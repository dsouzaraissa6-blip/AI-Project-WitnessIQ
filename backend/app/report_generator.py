"""
WitnessIQ Report Generator
Generates CSV and PDF reports from analysis results.
"""
import csv
import io
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def generate_csv_report(case: Dict, analysis: Dict) -> bytes:
    """Generate a CSV report of discrepancies and extracted facts."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header section
    writer.writerow(["WitnessIQ Analysis Report"])
    writer.writerow(["Case:", case.get("title", "Unknown")])
    writer.writerow(["Reference ID:", case.get("reference_id", "")])
    writer.writerow(["Incident Date:", case.get("incident_date", "Not specified")])
    writer.writerow(["Analysis Date:", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")])
    writer.writerow([])
    writer.writerow(["IMPORTANT: This report contains potential discrepancies flagged by automated analysis."])
    writer.writerow(["It does NOT determine guilt, credibility, or factual truth."])
    writer.writerow(["All flagged items require human review."])
    writer.writerow([])

    # Summary
    summary = analysis.get("summary", {})
    writer.writerow(["--- ANALYSIS SUMMARY ---"])
    writer.writerow(["Statements Analyzed", summary.get("statements_analyzed", 0)])
    writer.writerow(["Related Pairs Found", summary.get("related_pairs_found", 0)])
    writer.writerow(["Discrepancies Flagged", summary.get("discrepancies_flagged", 0)])
    writer.writerow(["Unique Details", summary.get("unique_details_count", 0)])
    writer.writerow(["Analysis Method", summary.get("analysis_method", "")])
    writer.writerow([])

    # Discrepancies
    writer.writerow(["--- DISCREPANCY TABLE ---"])
    writer.writerow([
        "Category", "Witness A", "Witness A Value", "Witness B", "Witness B Value",
        "Classification", "Explanation", "Detection Method",
        "Similarity Score", "Review Status", "Review Note"
    ])
    for disc in analysis.get("discrepancies", []):
        writer.writerow([
            disc.get("category", ""),
            disc.get("witness_a_label", ""),
            disc.get("witness_a_text", ""),
            disc.get("witness_b_label", ""),
            disc.get("witness_b_text", ""),
            disc.get("classification", "").replace("_", " ").title(),
            disc.get("explanation", ""),
            disc.get("detection_method", ""),
            disc.get("similarity_score", ""),
            disc.get("review_status", "pending") or "pending",
            disc.get("review_note", "") or "",
        ])
    writer.writerow([])

    # Extracted Facts
    writer.writerow(["--- EXTRACTED FACTS ---"])
    writer.writerow(["Witness", "Type", "Value", "Source", "Sentence"])
    for fact in analysis.get("extracted_facts", []):
        writer.writerow([
            fact.get("witness_label", ""),
            fact.get("entity_type", ""),
            fact.get("value", ""),
            fact.get("source", ""),
            fact.get("sentence", ""),
        ])
    writer.writerow([])

    # Semantic Matches
    writer.writerow(["--- SEMANTIC MATCHES ---"])
    writer.writerow(["Witness A", "Sentence A", "Witness B", "Sentence B", "Similarity Score", "Method"])
    for match in analysis.get("semantic_matches", []):
        writer.writerow([
            match.get("witness_a", ""),
            match.get("sentence_a", ""),
            match.get("witness_b", ""),
            match.get("sentence_b", ""),
            match.get("similarity_score", ""),
            match.get("match_method", ""),
        ])

    return output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility


def generate_pdf_report(case: Dict, analysis: Dict) -> bytes:
    """Generate a PDF report. Requires reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            "Title", parent=styles["Title"],
            fontSize=18, spaceAfter=6, textColor=colors.HexColor("#1e3a5f")
        )
        heading_style = ParagraphStyle(
            "Heading", parent=styles["Heading2"],
            fontSize=12, spaceBefore=12, spaceAfter=4, textColor=colors.HexColor("#1e3a5f")
        )
        body_style = styles["Normal"]
        warn_style = ParagraphStyle(
            "Warning", parent=styles["Normal"],
            fontSize=9, textColor=colors.HexColor("#7c3d12"),
            backColor=colors.HexColor("#fef3c7"), borderPadding=4
        )

        # Title
        story.append(Paragraph("WitnessIQ Analysis Report", title_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3a5f")))
        story.append(Spacer(1, 0.3*cm))

        # Case info
        story.append(Paragraph(f"<b>Case:</b> {case.get('title', '')}", body_style))
        story.append(Paragraph(f"<b>Reference:</b> {case.get('reference_id', '')}", body_style))
        story.append(Paragraph(f"<b>Incident Date:</b> {case.get('incident_date', 'Not specified')}", body_style))
        story.append(Paragraph(
            f"<b>Analysis Date:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body_style
        ))
        story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph(
            "IMPORTANT: This report flags potential discrepancies for human review. "
            "It does NOT determine guilt, credibility, or factual truth.",
            warn_style
        ))
        story.append(Spacer(1, 0.5*cm))

        # Summary
        summary = analysis.get("summary", {})
        story.append(Paragraph("Analysis Summary", heading_style))
        summary_data = [
            ["Metric", "Value"],
            ["Statements Analyzed", str(summary.get("statements_analyzed", 0))],
            ["Related Pairs Found", str(summary.get("related_pairs_found", 0))],
            ["Discrepancies Flagged", str(summary.get("discrepancies_flagged", 0))],
            ["Unique Details", str(summary.get("unique_details_count", 0))],
        ]
        t = Table(summary_data, colWidths=[8*cm, 9*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

        # Discrepancies
        story.append(Paragraph("Discrepancy Table", heading_style))
        disc_data = [["Category", "Witness A", "A Value", "Witness B", "B Value", "Classification"]]
        for disc in analysis.get("discrepancies", []):
            disc_data.append([
                disc.get("category", "")[:20],
                disc.get("witness_a_label", "")[:15],
                disc.get("witness_a_text", "")[:25],
                disc.get("witness_b_label", "")[:15],
                disc.get("witness_b_text", "")[:25],
                disc.get("classification", "").replace("_", " ").title()[:20],
            ])
        if len(disc_data) > 1:
            dt = Table(disc_data, colWidths=[3*cm, 2.5*cm, 4*cm, 2.5*cm, 4*cm, 3.5*cm])
            dt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(dt)

        doc.build(story)
        return buffer.getvalue()

    except ImportError as exc:
        logger.warning("reportlab not available; PDF export cannot be generated.")
        raise ImportError("PDF export requires reportlab.") from exc
