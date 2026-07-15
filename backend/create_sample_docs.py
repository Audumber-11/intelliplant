import os
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfdoc import pageSymbol

# Register custom fonts if available, fallback to built-in
try:
    pdfmetrics.registerFont(pdfmetrics.TTFont('Inter', 'fonts/Inter-Regular.ttf'))
    pdfmetrics.registerFont(pdfmetrics.TTFont('JetBrainsMono', 'fonts/JetBrainsMono-Regular.ttf'))
    use_custom_fonts = True
except:
    use_custom_fonts = False

def save_pdf(text_content, filename, title=None):
    """Helper function to save text content as PDF"""
    os.makedirs("sample_docs", exist_ok=True)
    filepath = Path("sample_docs") / filename
    
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#D97706'),
        spaceAfter=12,
        alignment=1  # Center
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6B88AA'),
        spaceAfter=8,
        alignment=1
    )
    
    normal_style = styles['Normal']
    if use_custom_fonts:
        normal_style.fontName = 'JetBrainsMono'
        title_style.fontName = 'JetBrainsMono'
        subtitle_style.fontName = 'JetBrainsMono'
    
    # Add content
    if title:
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 6))
    
    # Add paragraphs
    for line in text_content:
        if line.startswith('---'):
            elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph(line, normal_style))
        elements.append(Spacer(1, 4))
    
    # Build PDF
    doc.build(elements)
    return str(filepath)

def create_pump_p101_manual():
    """Create Pump_P101_Operations_Manual.pdf with complete content"""
    content = [
        "PUMP P-101 OPERATIONS MANUAL",
        "Document Number: OM-MECH-P101-003",
        "Revision: 2.1",
        "Effective Date: 15 March 2025",
        "",
        "=== EQUIPMENT SPECIFICATIONS ===",
        "Tag: P-101",
        "Service: Cooling Water Circulation", 
        "Type: Centrifugal End Suction",
        "Flow Rate: 250 m³/hr",
        "Total Head: 45m",
        "Power: 37 kW",
        "Pressure: 4.5 bar g",
        "Temperature: 45°C",
        "Seal Type: John Crane Type 21",
        "Bearing DE: SKF 6314",
        "Bearing NDE: SKF 6311",
        "",
        "=== STARTUP PROCEDURE ===",
        "1. Verify pump is primed with water",
        "2. Check seal flush system F-101 is operational",
        "3. Open suction valve V-101A fully",
        "4. Check coupling guard is properly secured",
        "5. Open minimum flow bypass V-101C to 25%",
        "6. Start motor and verify rotation direction",
        "7. Slowly open discharge valve V-101B",
        "8. Record flow FI-101 target 240-260 m³/hr",
        "9. Record bearing temperature max 70°C in shift log",
        "",
        "=== SHUTDOWN PROCEDURE ===",
        "1. Close discharge valve V-101B",
        "2. Stop motor",
        "3. Open minimum flow bypass V-101C to 100%",
        "4. Drain pump casing",
        "5. Close suction valve V-101A",
        "6. Lockout/tagout according to LOTO procedure",
        "",
        "=== FAULT CODES ===",
        "CODE\\tDESCRIPTION\\tCAUSE\\tACTION",
        "E-101\\tHigh Bearing Temperature\\tInsufficient lubrication\\tCheck oil level and replace if needed",
        "E-102\\tSeal Leakage\\tWorn sealing components\\tReplace seal kit",
        "E-103\\tLow Flow Rate\\tBlocked suction strainer\\tClean strainer",
        "E-104\\tMotor Overcurrent\\tMechanical binding\\tInspect impeller",
        "E-105\\tVibration\\tMisalignment\\tRealign coupling"
    ]
    return save_pdf(content, "Pump_P101_Operations_Manual.pdf", "Pump P-101 Operations Manual")

def create_maintenance_log_2024():
    """Create Maintenance_Log_2024.pdf with complete content"""
    content = [
        "PLANT MAINTENANCE LOG FY 2024",
        "",
        "Date\\tEquipment Tag\\tWO Number\\tWork Performed\\tTechnician\\tHours",
        "2024-01-15\\tP-101\\tWO-2024-045\\tBearing Replacement\\tJ. Smith\\t4.5",
        "2024-02-03\\tP-102\\tWO-2024-112\\tSeal Inspection\\tR. Patel\\t2.0",
        "2024-03-12\\tHE-201\\tWO-2024-228\\tHeat Exchanger Cleaning\\tM. Chen\\t6.0",
        "2024-04-18\\tHE-202\\tWO-2024-315\\tCoupling Alignment\\tJ. Smith\\t3.0",
        "2024-05-22\\tV-301\\tWO-2024-402\\tPRV Test\\tR. Patel\\t1.5",
        "2024-06-10\\tP-101\\tWO-2024-518\\tImpeller Inspection\\tM. Chen\\t3.5",
        "2024-07-05\\tC-101\\tWO-2024-627\\tCompressor Filter Change\\tJ. Smith\\t1.0",
        "2024-08-17\\tP-102\\tWO-2024-714\\tBearing Lubrication\\tR. Patel\\t1.5",
        "2024-09-23\\tHE-301\\tWO-2024-832\\tHeat Exchanger Inspection\\tM. Chen\\t4.0",
        "2024-10-09\\tV-301\\tWO-2024-901\\tActuator Calibration\\tJ. Smith\\t2.5",
        "2024-11-14\\tP-101\\tWO-2024-1019\\tSeal Replacement\\tR. Patel\\t3.0",
        "2024-12-01\\tP-102\\tWO-2024-1102\\tCoupling Lubrication\\tM. Chen\\t1.5",
        "2024-12-15\\tHE-201\\tWO-2024-1189\\tFilter Replacement\\tJ. Smith\\t0.5"
    ]
    return save_pdf(content, "Maintenance_Log_2024.pdf")

def create_safety_sop_confined_space():
    """Create Safety_SOP_Confined_Space.pdf with complete content"""
    content = [
        "SAFE WORK PROCEDURE - CONFINED SPACE ENTRY",
        "SOP Number: SWP-HS-003",
        "Effective Date: 1 January 2025",
        "",
        "=== PPE REQUIREMENTS ===",
        "• Gas Detector (H2S, O2, CO, LEL)",
        "• SCBA (Self-Contained Breathing Apparatus)",
        "• Safety Harness and Lifeline",
        "• Intrinsically Safe Radio",
        "• Hard Hat",
        "• Safety Boots",
        "",
        "=== GAS TESTING LIMITS ===",
        "• H2S: Less than 10 ppm",
        "• O2: Between 19.5 and 23.5 percent",
        "• LEL: Less than 10 percent",
        "• CO: Less than 25 ppm",
        "",
        "=== EMERGENCY ACTIONS ===",
        "If limit exceeded:",
        "1. Immediately evacuate area",
        "2. Initiate emergency shutdown",
        "3. Notify Control Room",
        "4. Establish decontamination zone",
        "",
        "=== CONFINED SPACE ENTRY PROCEDURE ===",
        "1. Obtain Permit-to-Work authorization",
        "2. Verify LOTO isolation is complete",
        "3. Conduct initial gas testing",
        "4. Ensure forced ventilation for minimum 10 minutes",
        "5. Re-test atmosphere",
        "6. Brief all entrants on hazards and procedures",
        "7. Constant atmospheric monitoring during operation",
        "8. Maintain standby person outside",
        "9. Emergency communication check",
        "10. Post-entry debrief and documentation",
        "",
        "=== RESCUE PROCEDURE ===",
        "1. Stop all operations immediately",
        "2. Notify emergency response team",
        "3. Deploy rescue equipment",
        "4. Perform non-entry rescue if conditions unsafe",
        "5. Document incident and corrective actions"
    ]
    return save_pdf(content, "Safety_SOP_Confined_Space.pdf", "Confined Space Entry SOP")

def create_heat_exchanger_register():
    """Create Heat_Exchanger_Register.pdf with complete content"""
    content = [
        "HEAT EXCHANGER INSPECTION REGISTER",
        "Document ID: PR-HE-001",
        "Effective Date: 1 February 2025",
        "",
        "=== INSTRUMENTATION ===",
        "Tag\\tService\\tArea\\tDesign Pressure\\tLast Inspection Date\\tNext Due Date\\tInspector\\tStatus",
        "HE-201\\tCooling\\tUnit 2\\t15 bar\\t2024-03-15\\t2026-02-15\\tM. Chen\\tActive",
        "HE-202\\tHeating\\tUnit 3\\t12 bar\\t2024-06-20\\t2026-06-20\\tR. Patel\\tActive",
        "HE-301\\tCooling\\tUnit 1\\t20 bar\\t2023-12-10\\t2025-01-10\\tJ. Smith\\tOVERDUE",
        "HE-302\\tPreheating\\tUnit 4\\t18 bar\\t2024-01-30\\t2026-01-30\\tM. Chen\\tActive",
        "HE-401\\tCooling\\tUnit 5\\t16 bar\\t2024-08-05\\t2026-08-05\\tR. Patel\\tActive",
        "HE-501\\tHeating\\tUnit 2\\t22 bar\\t2023-09-12\\t2025-09-12\\tJ. Smith\\tOVERDUE",
        "HE-502\\tCooling\\tUnit 1\\t14 bar\\t2025-02-28\\t2027-02-28\\tM. Chen\\tActive",
        "HE-601\\tPreheating\\tUnit 4\\t19 bar\\t2024-11-01\\t2026-11-01\\tR. Patel\\tActive",
        "",
        "WARNING: HE-301 and HE-501 are OVERDUE for inspection and require immediate shutdown planning"
    ]
    return save_pdf(content, "Heat_Exchanger_Register.pdf", "Heat Exchanger Register")

def create_incident_report_jan2025():
    """Create Incident_Report_Jan2025.pdf with complete content"""
    content = [
        "INCIDENT INVESTIGATION REPORT",
        "Report No: IIR-2025-001",
        "Date: 15 January 2025",
        "Location: Unit 2 CV-201 and V-301",
        "",
        "Classification: HIGH POTENTIAL",
        "No Injuries Reported",
        "",
        "=== INCIDENT DESCRIPTION ===",
        "Control valve CV-201 failed open resulting in vessel V-301 overpressuring to 18.2 bar vs design 15 bar. Pressure relief valve PRV-301 activated. Operator initiated emergency shutdown ESD at 14:37, unit down 4.5 hours.",
        "",
        "=== ROOT CAUSE ANALYSIS ===",
        "5-Why Analysis:",
        "1. CV-201 failed open",
        "2. Spring fatigue fracture",
        "3. Spring was 7 years old vs 5 year recommended replacement",
        "4. No preventive maintenance task existed",
        "5. OEM manual recommendations not loaded to maintenance system at commissioning in 2018",
        "",
        "=== CORRECTIVE ACTIONS ===",
        "1. Replace CV-201 completed 17-Jan-2025",
        "2. Create PM tasks for all 47 control valve actuators",
        "3. Audit all OEM manuals",
        "4. Lower alarm setpoint from 16 to 14 bar",
        "5. Operator training refresher",
        "6. Recertify PRV-301",
        "",
        "=== LESSONS LEARNED ===",
        "1. Critical equipment requires OEM manual compliance",
        "2. Preventive maintenance scheduling must account for OEM recommendations",
        "3. Alarm thresholds should be conservative for safety",
        "4. Documentation must be integrated with maintenance systems",
        "5. Regular equipment audits prevent component failure"
    ]
    return save_pdf(content, "Incident_Report_Jan2025.pdf", "Incident Report January 2025")

if __name__ == "__main__":
    # Create sample_docs directory if it doesn't exist
    os.makedirs("sample_docs", exist_ok=True)
    
    print("Creating sample documents...")
    
    # Generate all 5 PDFs
    file1 = create_pump_p101_manual()
    file2 = create_maintenance_log_2024()
    file3 = create_safety_sop_confined_space()
    file4 = create_heat_exchanger_register()
    file5 = create_incident_report_jan2025()
    
    created_files = [file1, file2, file3, file4, file5]
    
    print("\nGenerated files:")
    for f in created_files:
        size = os.path.getsize(f)
        print(f"  {os.path.basename(f)}: {size:,} bytes")
    
    print(f"\nTotal documents created: {len(created_files)}")
    
    # Verify all files exist
    sample_dir = Path("sample_docs")
    pdf_files = list(sample_dir.glob("*.pdf"))
    
    if len(pdf_files) == 5:
        print(f"\n✅ SUCCESS: Created {len(pdf_files)} PDF files in sample_docs/")
        print("Files created:")
        for pdf in sorted(pdf_files):
            print(f"  - {pdf.name}")
    else:
        print(f"\n❌ ERROR: Expected 5 PDF files, but created {len(pdf_files)}")
        print("Missing files:", pdf_files)