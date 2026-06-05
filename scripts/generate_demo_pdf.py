"""Generate a realistic automotive engineering spec PDF for the live demo.

Produces an Electric Power Steering (EPS) control module specification with a
state-machine diagram plus DTC, CAN signal, and calibration parameter tables.
The PDF is intentionally "unstructured" the way a real spec is: a human reads
the diagram and tables, but nothing is queryable until the pipeline ingests it.

Run::

    uv run python scripts/generate_demo_pdf.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "source_documents"
    / "demo"
    / "eps_control_module_spec.pdf"
)

# Ford brand palette
FORD_BLUE = colors.HexColor("#066FEF")
FORD_DARK = colors.HexColor("#00095B")
INK = colors.HexColor("#1a1a1a")
GREY = colors.HexColor("#555555")
LINE = colors.HexColor("#c4cad2")
BG_BLUE = colors.HexColor("#eef4fe")
HEAD_BG = colors.HexColor("#00095B")


# --- Document metadata (also embedded in the body text so the parser finds it) ---
DOC_ID = "FNV-EPS-4521"
TITLE = "Electric Power Steering Control Module Specification"
REVISION = "C"
SUBSYSTEM = "Chassis / Steering"
ASIL = "ASIL D"
EFFECTIVE_DATE = "2026-04-15"


# --- Diagnostic Trouble Codes ---
DTC_ROWS = [
    ["DTC Code", "Description", "Fault Action", "MIL", "Debounce (ms)"],
    ["C1511", "Torque Sensor Signal Implausible", "Disable assist, latch", "Yes", "200"],
    ["C1513", "Motor Phase U Open Circuit", "Derate to 40%", "Yes", "500"],
    ["C1515", "Motor Over-Temperature", "Thermal derate", "No", "1000"],
    ["C1521", "Steering Angle Sensor No Comms", "Inhibit assist", "Yes", "300"],
    ["U0126", "Lost Comms with SAS Module", "Use estimated angle", "No", "400"],
    ["P0AA6", "HV System Isolation Fault", "Open contactors", "Yes", "100"],
    ["C1A00", "ECU Internal Watchdog Reset", "Safe-state, reset", "Yes", "50"],
]

# --- CAN Signals ---
SIGNAL_ROWS = [
    ["Signal Name", "Message ID", "Start Bit", "Length", "Scale", "Unit", "Cycle (ms)"],
    ["EPS_AssistTorque", "0x1A4", "0", "12", "0.1", "Nm", "10"],
    ["EPS_MotorCurrent", "0x1A4", "12", "10", "0.05", "A", "10"],
    ["EPS_SteeringAngle", "0x0C8", "0", "16", "0.0625", "deg", "10"],
    ["EPS_AngleRate", "0x0C8", "16", "12", "0.25", "deg/s", "10"],
    ["EPS_ModuleState", "0x2F0", "0", "4", "1", "enum", "100"],
    ["EPS_TempMotor", "0x2F0", "8", "8", "1", "degC", "100"],
    ["EPS_FaultActive", "0x2F0", "16", "1", "1", "bool", "100"],
]

# --- Calibration Parameters ---
PARAM_ROWS = [
    ["Parameter ID", "Name", "Min", "Max", "Default", "Unit"],
    ["K_ASSIST_GAIN", "Base Assist Gain", "0.5", "3.0", "1.8", "Nm/Nm"],
    ["K_RETURN_GAIN", "Active Return Gain", "0.0", "1.5", "0.6", "-"],
    ["K_DAMP_HI", "High-Speed Damping", "0.0", "2.0", "0.9", "Nm/(deg/s)"],
    ["T_DERATE_ON", "Thermal Derate Onset", "90", "140", "115", "degC"],
    ["T_DERATE_OFF", "Thermal Derate Recovery", "70", "120", "95", "degC"],
    ["V_ASSIST_MAX", "Max Assist Speed", "60", "250", "200", "kph"],
]

# --- State machine for the "look how tricky this is" diagram ---
# (name, x, y) box centers in a 540 x 230 drawing
STATES = [
    ("INIT", 70, 180),
    ("STANDBY", 230, 180),
    ("ASSIST\nACTIVE", 400, 180),
    ("DERATE", 400, 60),
    ("FAULT", 230, 60),
]
TRANSITIONS = [
    (0, 1),  # INIT -> STANDBY
    (1, 2),  # STANDBY -> ASSIST ACTIVE
    (2, 3),  # ASSIST -> DERATE
    (3, 2),  # DERATE -> ASSIST
    (2, 4),  # ASSIST -> FAULT
    (3, 4),  # DERATE -> FAULT
    (4, 1),  # FAULT -> STANDBY
]
BOX_W, BOX_H = 96, 44


def _state_diagram() -> Drawing:
    d = Drawing(540, 230)
    centers = {i: (x, y) for i, (_, x, y) in enumerate(STATES)}

    # Arrows first (so boxes sit on top)
    for src, dst in TRANSITIONS:
        x1, y1 = centers[src]
        x2, y2 = centers[dst]
        d.add(Line(x1, y1, x2, y2, strokeColor=LINE, strokeWidth=1.4))
        # arrowhead
        import math

        ang = math.atan2(y2 - y1, x2 - x1)
        # land the head on the box edge, not the center
        hx = x2 - math.cos(ang) * (BOX_W / 2 + 4)
        hy = y2 - math.sin(ang) * (BOX_H / 2 + 4)
        size = 6
        left = (hx - size * math.cos(ang - 0.5), hy - size * math.sin(ang - 0.5))
        right = (hx - size * math.cos(ang + 0.5), hy - size * math.sin(ang + 0.5))
        d.add(
            Polygon(
                points=[hx, hy, left[0], left[1], right[0], right[1]],
                fillColor=FORD_BLUE,
                strokeColor=FORD_BLUE,
            )
        )

    for i, (name, x, y) in enumerate(STATES):
        fill = BG_BLUE if name != "FAULT" else colors.HexColor("#fef0ed")
        edge = FORD_BLUE if name != "FAULT" else colors.HexColor("#c5280c")
        d.add(
            Rect(
                x - BOX_W / 2,
                y - BOX_H / 2,
                BOX_W,
                BOX_H,
                rx=8,
                ry=8,
                fillColor=fill,
                strokeColor=edge,
                strokeWidth=1.4,
            )
        )
        lines = name.split("\n")
        for li, ln in enumerate(lines):
            d.add(
                String(
                    x,
                    y - 4 + (len(lines) - 1) * 6 - li * 12,
                    ln,
                    textAnchor="middle",
                    fontName="Helvetica-Bold",
                    fontSize=9,
                    fillColor=FORD_DARK,
                )
            )
    return d


def _table(rows: list[list[str]], col_widths: list[float]) -> Table:
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("TEXTCOLOR", (0, 1), (-1, -1), INK),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f8fa")]),
                ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def build() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], textColor=FORD_DARK, fontName="Helvetica-Bold",
        fontSize=18, spaceAfter=4,
    )
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], textColor=FORD_DARK, fontName="Helvetica-Bold",
        fontSize=12, spaceBefore=14, spaceAfter=6,
    )
    meta = ParagraphStyle(
        "Meta", parent=styles["Normal"], textColor=GREY, fontSize=9, leading=14,
    )
    body = ParagraphStyle(
        "Body", parent=styles["Normal"], textColor=INK, fontSize=9.5, leading=14,
        spaceAfter=6,
    )

    story: list[object] = []
    story.append(Paragraph(TITLE, h1))
    story.append(
        Paragraph(
            f"Document ID: {DOC_ID} &nbsp;&nbsp;|&nbsp;&nbsp; Revision: {REVISION} "
            f"&nbsp;&nbsp;|&nbsp;&nbsp; Subsystem: {SUBSYSTEM}<br/>"
            f"Safety Classification: {ASIL} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Effective Date: {EFFECTIVE_DATE}",
            meta,
        )
    )
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "This specification defines the control logic, diagnostic coverage, "
            "communication signals, and calibration parameters for the Electric "
            "Power Steering (EPS) control module. The assist state machine governs "
            "transitions between standby, active assist, thermal derate, and fault "
            "handling. All diagnostic trouble codes are debounced per the table below.",
            body,
        )
    )

    story.append(Paragraph("1. Assist State Machine", h2))
    story.append(
        Paragraph(
            "The module transitions through the following states. Note the multiple "
            "paths into FAULT and the recovery path back to STANDBY \u2014 reconstructing "
            "this from prose alone is error-prone.",
            body,
        )
    )
    story.append(_state_diagram())

    story.append(Paragraph("2. Diagnostic Trouble Codes (DTC Matrix)", h2))
    story.append(
        _table(
            DTC_ROWS,
            [0.8 * inch, 2.1 * inch, 1.7 * inch, 0.5 * inch, 1.0 * inch],
        )
    )

    story.append(Paragraph("3. CAN Signal Definitions", h2))
    story.append(
        _table(
            SIGNAL_ROWS,
            [1.5 * inch, 0.9 * inch, 0.7 * inch, 0.65 * inch, 0.6 * inch, 0.6 * inch, 0.7 * inch],
        )
    )

    story.append(Paragraph("4. Calibration Parameters", h2))
    story.append(
        _table(
            PARAM_ROWS,
            [1.4 * inch, 1.9 * inch, 0.6 * inch, 0.6 * inch, 0.7 * inch, 0.9 * inch],
        )
    )

    doc = SimpleDocTemplate(
        str(OUT_PATH),
        pagesize=letter,
        title=TITLE,
        author="Ford Motor Company",
        subject=DOC_ID,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )
    doc.build(story)
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
