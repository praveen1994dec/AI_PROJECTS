"""
Report generator for PDF and CSV exports of analysis results.
Uses reportlab for PDF and built-in csv module for CSV.
"""
import csv
import io
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def _format_currency(value: Any) -> str:
    """Format a value as currency."""
    try:
        if isinstance(value, str):
            val = float(value)
        else:
            val = float(value)
        return f"${val:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


def _format_percentage(value: Any) -> str:
    """Format a value as percentage."""
    try:
        if isinstance(value, str):
            val = float(value)
        else:
            val = float(value)
        return f"{val:.1f}%"
    except (ValueError, TypeError):
        return "0.0%"


def generate_pdf(analysis: Dict[str, Any], stream: io.BytesIO) -> None:
    """
    Generate a PDF report from analysis data.
    
    Args:
        analysis: Dictionary containing analysis, cost_summary, and metadata
        stream: BytesIO object to write PDF to
    """
    doc = SimpleDocTemplate(stream, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    
    heading_style = ParagraphStyle(
        'SectionHead',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        fontName='Helvetica-Bold',
        spaceBefore=12,
    )
    
    # Header
    region = analysis.get("region", "Unknown")
    created_at = analysis.get("created_at", datetime.now())
    if isinstance(created_at, str):
        created_at_str = created_at
    else:
        created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    story.append(Paragraph("AI Cloud Cost Detective", title_style))
    story.append(Paragraph(f"Analysis Report - {region}", styles['Heading2']))
    story.append(Paragraph(f"Generated: {created_at_str}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Cost Summary Section
    cost_summary = analysis.get("cost_summary", {})
    if cost_summary:
        story.append(Paragraph("Cost Summary", heading_style))
        
        current = cost_summary.get("current", {})
        previous = cost_summary.get("previous_month", {})
        forecast = cost_summary.get("forecast", {})
        
        current_total = _format_currency(current.get("total", 0))
        previous_total = _format_currency(previous.get("total", 0))
        forecast_total = _format_currency(forecast.get("total", 0))
        
        summary_data = [
            ["Metric", "Amount"],
            ["Current Month-to-Date", current_total],
            ["Previous Month Total", previous_total],
            ["15-Day Forecast", forecast_total],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Top Resources Section
    top_resources = cost_summary.get("top_resources", [])
    if top_resources:
        story.append(Paragraph("Top 10 Cost-Driving Resources", heading_style))
        
        resources_data = [["Resource Name", "Type", "Region", "Cost", "Cost Basis"]]
        for i, resource in enumerate(top_resources[:10]):
            name = resource.get("name", resource.get("resource_id", "Unknown"))
            rtype = resource.get("resource_type", "Unknown")
            rregion = resource.get("region", "N/A")
            cost = _format_currency(resource.get("cost", 0))
            basis = resource.get("cost_basis", "estimated")
            resources_data.append([name, rtype, rregion, cost, basis])
        
        resources_table = Table(resources_data, colWidths=[2*inch, 1.2*inch, 1*inch, 1*inch, 0.8*inch])
        resources_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(resources_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Anomalies Section
    anomalies = cost_summary.get("anomalies", {})
    if isinstance(anomalies, dict) and anomalies.get("anomalies"):
        story.append(Paragraph("Detected Cost Anomalies", heading_style))
        
        anomalies_data = [["Date", "Service", "Amount", "% Change", "Severity"]]
        for anomaly in anomalies.get("anomalies", [])[:10]:
            date_str = anomaly.get("date", "N/A")
            service = anomaly.get("service", "N/A")
            amount = _format_currency(anomaly.get("amount", 0))
            pct_change = _format_percentage(anomaly.get("pct_change", 0))
            severity = anomaly.get("severity", "medium").upper()
            anomalies_data.append([date_str, service, amount, pct_change, severity])
        
        if len(anomalies_data) > 1:
            anomalies_table = Table(anomalies_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.2*inch, 0.8*inch])
            anomalies_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            story.append(anomalies_table)
            story.append(Spacer(1, 0.2*inch))
    
    # AI Analysis Issues Section
    ai_analysis = analysis.get("analysis_result", {})
    if isinstance(ai_analysis, dict):
        issues = ai_analysis.get("issues", [])
        if issues:
            story.append(PageBreak())
            story.append(Paragraph("Optimization Issues & Recommendations", heading_style))
            
            for issue in issues[:20]:  # Limit to 20 issues per page
                issue_type = issue.get("type", "unknown").upper()
                severity = issue.get("severity", "medium").upper()
                resource = issue.get("resource", "N/A")
                savings = _format_currency(issue.get("estimated_monthly_savings", 0))
                description = issue.get("description", "No description")
                fix_command = issue.get("fix_command", "No fix command available")
                
                # Issue header
                issue_title = f"{issue_type} - {resource} [{severity}]"
                story.append(Paragraph(issue_title, styles['Heading3']))
                story.append(Paragraph(f"<b>Description:</b> {description}", styles['Normal']))
                story.append(Paragraph(f"<b>Estimated Monthly Savings:</b> {savings}", styles['Normal']))
                story.append(Paragraph(f"<b>Fix Command:</b>", styles['Normal']))
                story.append(Paragraph(f"<code>{fix_command}</code>", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
    
    # Footer with total savings
    if isinstance(ai_analysis, dict):
        total_savings = ai_analysis.get("total_estimated_monthly_savings", 0)
        total_savings_str = _format_currency(total_savings)
        yearly_savings = float(total_savings) * 12
        yearly_savings_str = _format_currency(yearly_savings)
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("<b>Total Estimated Monthly Savings:</b> " + total_savings_str, styles['Normal']))
        story.append(Paragraph("<b>Total Estimated Yearly Savings:</b> " + yearly_savings_str, styles['Normal']))
    
    # Build PDF
    doc.build(story)


def generate_csv(analysis: Dict[str, Any], stream: io.StringIO) -> None:
    """
    Generate a CSV report from analysis data.
    Multiple sections flattened into rows.
    
    Args:
        analysis: Dictionary containing analysis, cost_summary, and metadata
        stream: StringIO object to write CSV to
    """
    writer = csv.writer(stream)
    
    # Header
    writer.writerow(["AI Cloud Cost Detective - Analysis Report"])
    writer.writerow(["Region", analysis.get("region", "Unknown")])
    writer.writerow(["Generated", analysis.get("created_at", datetime.now())])
    writer.writerow([])
    
    # Cost Summary Section
    cost_summary = analysis.get("cost_summary", {})
    writer.writerow(["COST SUMMARY"])
    writer.writerow(["Metric", "Amount"])
    
    current = cost_summary.get("current", {})
    previous = cost_summary.get("previous_month", {})
    forecast = cost_summary.get("forecast", {})
    
    writer.writerow(["Current Month-to-Date", _format_currency(current.get("total", 0))])
    writer.writerow(["Previous Month Total", _format_currency(previous.get("total", 0))])
    writer.writerow(["15-Day Forecast", _format_currency(forecast.get("total", 0))])
    writer.writerow([])
    
    # Top Resources Section
    top_resources = cost_summary.get("top_resources", [])
    if top_resources:
        writer.writerow(["TOP 10 COST-DRIVING RESOURCES"])
        writer.writerow(["Resource Name", "Type", "Region", "Cost", "Cost Basis"])
        for resource in top_resources[:10]:
            name = resource.get("name", resource.get("resource_id", "Unknown"))
            rtype = resource.get("resource_type", "Unknown")
            rregion = resource.get("region", "N/A")
            cost = _format_currency(resource.get("cost", 0))
            basis = resource.get("cost_basis", "estimated")
            writer.writerow([name, rtype, rregion, cost, basis])
        writer.writerow([])
    
    # Anomalies Section
    anomalies = cost_summary.get("anomalies", {})
    if isinstance(anomalies, dict) and anomalies.get("anomalies"):
        writer.writerow(["DETECTED COST ANOMALIES"])
        writer.writerow(["Date", "Service", "Amount", "% Change", "Severity"])
        for anomaly in anomalies.get("anomalies", [])[:10]:
            date_str = anomaly.get("date", "N/A")
            service = anomaly.get("service", "N/A")
            amount = _format_currency(anomaly.get("amount", 0))
            pct_change = _format_percentage(anomaly.get("pct_change", 0))
            severity = anomaly.get("severity", "medium")
            writer.writerow([date_str, service, amount, pct_change, severity])
        writer.writerow([])
    
    # AI Analysis Issues Section
    ai_analysis = analysis.get("analysis_result", {})
    if isinstance(ai_analysis, dict):
        issues = ai_analysis.get("issues", [])
        if issues:
            writer.writerow(["OPTIMIZATION ISSUES & RECOMMENDATIONS"])
            writer.writerow(["Type", "Resource", "Severity", "Description", "Estimated Monthly Savings", "Fix Command"])
            for issue in issues:
                issue_type = issue.get("type", "unknown")
                severity = issue.get("severity", "medium")
                resource = issue.get("resource", "N/A")
                description = issue.get("description", "No description")
                savings = _format_currency(issue.get("estimated_monthly_savings", 0))
                fix_command = issue.get("fix_command", "No fix command available")
                writer.writerow([issue_type, resource, severity, description, savings, fix_command])
            writer.writerow([])
    
    # Summary
    if isinstance(ai_analysis, dict):
        total_savings = ai_analysis.get("total_estimated_monthly_savings", 0)
        yearly_savings = float(total_savings) * 12
        writer.writerow(["SUMMARY"])
        writer.writerow(["Total Estimated Monthly Savings", _format_currency(total_savings)])
        writer.writerow(["Total Estimated Yearly Savings", _format_currency(yearly_savings)])
