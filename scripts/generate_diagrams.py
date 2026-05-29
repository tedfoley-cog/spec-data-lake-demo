"""Generate realistic automotive engineering diagrams for source documents.

Creates PNG diagrams using Graphviz:
- PCM power mode state machine
- Transmission shift logic flow chart
- CAN bus network topology
"""

import subprocess
import textwrap
from pathlib import Path

DIAGRAM_DIR = Path("source_documents/pdf_specs/diagrams")


def generate_pcm_state_machine() -> None:
    """Generate a PCM power mode state machine diagram."""
    dot = textwrap.dedent("""\
    digraph PCM_Power_Modes {
        rankdir=TB;
        fontname="Helvetica";
        fontsize=14;
        label="\\nPCM Power Mode State Machine\\nDocument: ES-PCM-2024-001 Rev C  |  ASIL-B  |  ISO 26262 Compliant\\n";
        labelloc=t;
        bgcolor="#fafafa";
        pad=0.5;
        nodesep=0.6;
        ranksep=0.8;

        node [
            shape=rectangle,
            style="rounded,filled",
            fontname="Helvetica",
            fontsize=11,
            width=2.2,
            height=0.7
        ];
        edge [fontname="Helvetica", fontsize=9];

        OFF [label="OFF\\n(Mode 0x00)\\nAll systems disabled", fillcolor="#e8e8e8"];
        ACC [label="ACCESSORY\\n(Mode 0x01)\\nInfotainment active", fillcolor="#d4e6f1"];
        RUN [label="RUN\\n(Mode 0x02)\\nAll ECUs active", fillcolor="#aed6f1"];
        CRANK [label="CRANK\\n(Mode 0x03)\\nStarter engaged", fillcolor="#f9e79f"];
        RUN_ENGINE [label="RUN + ENGINE\\n(Mode 0x04)\\nNormal operation", fillcolor="#abebc6"];
        EMERGENCY [label="EMERGENCY STOP\\n(Mode 0x05)\\nFault shutdown", fillcolor="#f5b7b1"];

        // Normal transitions
        OFF -> ACC [label="IGN_SW = ACC\\nBATT_V > 9.0V", color="#2980b9"];
        ACC -> RUN [label="IGN_SW = RUN\\nBATT_V > 10.5V", color="#2980b9"];
        RUN -> CRANK [label="START_REQ = 1\\nTRANS_RANGE = P/N\\nBRAKE = ON", color="#27ae60"];
        CRANK -> RUN_ENGINE [label="ENGINE_RPM > 400\\nt < 10s", color="#27ae60"];
        RUN_ENGINE -> RUN [label="ENGINE_STALL\\nRPM < 200 for 2s", color="#e67e22"];

        // Reverse transitions
        RUN -> ACC [label="IGN_SW = ACC", color="#7f8c8d", style=dashed];
        ACC -> OFF [label="IGN_SW = OFF", color="#7f8c8d", style=dashed];
        RUN -> OFF [label="IGN_SW = OFF\\nDirect shutdown", color="#7f8c8d", style=dashed];

        // Emergency transitions
        RUN_ENGINE -> EMERGENCY [label="FAULT_CRITICAL = 1\\nOIL_PRESS < 5 psi\\nor COOLANT > 120°C", color="#c0392b", penwidth=2];
        CRANK -> EMERGENCY [label="CRANK_TIMEOUT\\nt > 10s", color="#c0392b", penwidth=2];
        EMERGENCY -> OFF [label="FAULT_CLEARED\\nManual reset req'd", color="#c0392b", style=dashed];

        // Timeout from crank
        CRANK -> RUN [label="CRANK_ABORT\\nSTART_REQ = 0", color="#e67e22", style=dashed];

        // Legend
        subgraph cluster_legend {
            label="Transition Legend";
            style=rounded;
            color="#bdc3c7";
            fontsize=10;
            node [shape=plaintext, width=0, height=0, fontsize=9];
            leg1 [label=""];
            leg2 [label=""];
            leg3 [label=""];
            leg1 -> leg2 [label="Normal forward", color="#2980b9"];
            leg2 -> leg3 [label="Reverse / timeout", color="#7f8c8d", style=dashed];
            leg3 -> leg1 [label="Emergency", color="#c0392b", penwidth=2, style=invis];
        }
    }
    """)
    dot_file = DIAGRAM_DIR / "pcm_state_machine.dot"
    dot_file.write_text(dot)
    subprocess.run(
        ["dot", "-Tpng", "-Gdpi=150", str(dot_file), "-o", str(DIAGRAM_DIR / "pcm_state_machine.png")],
        check=True,
    )
    dot_file.unlink()
    print("  Generated: pcm_state_machine.png")


def generate_shift_logic_flow() -> None:
    """Generate a transmission shift logic flow diagram."""
    dot = textwrap.dedent("""\
    digraph Shift_Logic {
        rankdir=TB;
        fontname="Helvetica";
        fontsize=14;
        label="\\nTransmission Shift Logic — Gear Range Selection\\nDocument: ES-TRANS-2024-002 Rev B  |  ASIL-B\\n";
        labelloc=t;
        bgcolor="#fafafa";
        pad=0.5;
        nodesep=0.5;
        ranksep=0.7;

        node [fontname="Helvetica", fontsize=10];
        edge [fontname="Helvetica", fontsize=8];

        // Decision nodes
        node [shape=diamond, style=filled, fillcolor="#fadbd8", width=2.5, height=1.0];
        D1 [label="Shift lever\\nposition?"];
        D2 [label="Vehicle speed\\n< 5 mph?"];
        D3 [label="Brake pedal\\napplied?"];
        D4 [label="Shift button\\npressed?"];
        D5 [label="Engine RPM\\nin range?"];
        D6 [label="Torque\\nconverter\\nlocked?"];
        D7 [label="Current gear\\n= target?"];

        // Process nodes
        node [shape=rectangle, style="rounded,filled", fillcolor="#d5f5e3", width=2.0, height=0.6];
        P1 [label="Read PRNDL\\nsensor input"];
        P2 [label="Validate shift\\npreconditions"];
        P3 [label="Disengage\\ntorque converter"];
        P4 [label="Command\\nsolenoid pack"];
        P5 [label="Monitor gear\\nengagement"];
        P6 [label="Re-engage\\ntorque converter"];
        P7 [label="Update PCM\\nstatus CAN msg"];
        P8 [label="Set DTC\\nP0700"];

        // Terminal nodes
        node [shape=rectangle, style="rounded,filled", fillcolor="#d4e6f1", width=1.8, height=0.5];
        START [label="Shift Request\\nReceived"];
        END_OK [label="Shift Complete\\nGear Engaged"];
        END_FAIL [label="Shift Rejected\\nDTC Logged"];

        // Flow
        START -> P1;
        P1 -> D1;
        D1 -> D2 [label="R, D, or N"];
        D1 -> END_FAIL [label="Invalid\\nposition"];
        D2 -> D3 [label="Yes"];
        D2 -> END_FAIL [label="No (> 5 mph)"];
        D3 -> P2 [label="Yes"];
        D3 -> END_FAIL [label="No"];
        P2 -> D5;
        D5 -> D6 [label="Yes"];
        D5 -> END_FAIL [label="Out of\\nrange"];
        D6 -> P3 [label="Yes"];
        D6 -> P4 [label="No"];
        P3 -> P4;
        P4 -> P5;
        P5 -> D7;
        D7 -> P6 [label="Yes"];
        D7 -> P8 [label="No\\n(timeout)"];
        P6 -> P7;
        P7 -> END_OK;
        P8 -> END_FAIL;

        // Subgraph for timing constraints
        subgraph cluster_timing {
            label="Timing Constraints";
            style=rounded;
            color="#bdc3c7";
            fontsize=9;
            node [shape=plaintext, fontsize=8, width=0, height=0];
            T1 [label="Solenoid response: < 50ms"];
            T2 [label="Gear engagement: < 300ms"];
            T3 [label="TC lockup: < 500ms"];
            T4 [label="Total shift time: < 1.2s"];
        }
    }
    """)
    dot_file = DIAGRAM_DIR / "shift_logic_flow.dot"
    dot_file.write_text(dot)
    subprocess.run(
        ["dot", "-Tpng", "-Gdpi=150", str(dot_file), "-o", str(DIAGRAM_DIR / "shift_logic_flow.png")],
        check=True,
    )
    dot_file.unlink()
    print("  Generated: shift_logic_flow.png")


def generate_can_topology() -> None:
    """Generate a CAN bus network topology diagram."""
    dot = textwrap.dedent("""\
    digraph CAN_Topology {
        rankdir=LR;
        fontname="Helvetica";
        fontsize=14;
        label="\\nVehicle CAN Bus Network Topology\\nDocument: ES-CAN-2024-003 Rev A  |  500 kbps High-Speed CAN\\n";
        labelloc=t;
        bgcolor="#fafafa";
        pad=0.5;
        nodesep=0.4;

        node [fontname="Helvetica", fontsize=9, shape=rectangle, style="rounded,filled"];
        edge [fontname="Helvetica", fontsize=8];

        // CAN Bus backbone
        node [fillcolor="#f8f9fa", width=0.3, height=3.5, shape=rectangle, style=filled];
        BUS_HS [label="HS-CAN\\n500 kbps", fillcolor="#fdebd0"];
        BUS_MS [label="MS-CAN\\n125 kbps", fillcolor="#d5f5e3"];
        GW [label="Gateway\\nECU", shape=rectangle, style="rounded,filled", fillcolor="#fadbd8", width=1.2, height=0.8];

        // HS-CAN ECUs
        node [fillcolor="#d4e6f1", width=1.8, height=0.7, shape=rectangle, style="rounded,filled"];
        PCM [label="PCM\\n0x100-0x1FF\\nPower Mode, RPM\\nThrottle, Fuel"];
        TCM [label="TCM\\n0x200-0x2FF\\nGear State, Shift\\nTorque Converter"];
        ABS [label="ABS/ESC\\n0x300-0x3FF\\nWheel Speed\\nBrake Pressure"];
        EPAS [label="EPAS\\n0x400-0x4FF\\nSteering Angle\\nTorque Assist"];
        BCM [label="BCM\\n0x500-0x5FF\\nIgnition State\\nDoor, Lights"];

        // MS-CAN ECUs
        node [fillcolor="#d5f5e3"];
        IPC [label="IPC\\n0x600-0x6FF\\nGauges, Telltales\\nOdometer"];
        HVAC [label="HVAC\\n0x700-0x7FF\\nClimate Control\\nBlower, Temp"];
        APIM [label="APIM\\n0x800-0x8FF\\nInfotainment\\nMedia, Nav"];

        // Connections
        PCM -> BUS_HS [dir=both, color="#2980b9"];
        TCM -> BUS_HS [dir=both, color="#2980b9"];
        ABS -> BUS_HS [dir=both, color="#2980b9"];
        EPAS -> BUS_HS [dir=both, color="#2980b9"];
        BCM -> BUS_HS [dir=both, color="#2980b9"];

        BUS_HS -> GW [dir=both, color="#e74c3c", penwidth=2, label="Bridge"];
        GW -> BUS_MS [dir=both, color="#e74c3c", penwidth=2, label="Bridge"];

        BUS_MS -> IPC [dir=both, color="#27ae60"];
        BUS_MS -> HVAC [dir=both, color="#27ae60"];
        BUS_MS -> APIM [dir=both, color="#27ae60"];

        // Signal table subgraph
        subgraph cluster_signals {
            label="Key Signal Summary (HS-CAN)";
            style=rounded;
            color="#bdc3c7";
            fontsize=9;
            node [shape=plaintext, fontsize=8, width=0, height=0];
            SIG [label=<
                <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">
                <TR><TD BGCOLOR="#34495e"><FONT COLOR="white"><B>Message ID</B></FONT></TD>
                    <TD BGCOLOR="#34495e"><FONT COLOR="white"><B>Signal</B></FONT></TD>
                    <TD BGCOLOR="#34495e"><FONT COLOR="white"><B>Bits</B></FONT></TD>
                    <TD BGCOLOR="#34495e"><FONT COLOR="white"><B>Rate</B></FONT></TD></TR>
                <TR><TD>0x120</TD><TD>EngineRPM</TD><TD>0-15</TD><TD>10ms</TD></TR>
                <TR><TD>0x121</TD><TD>VehicleSpeed</TD><TD>0-15</TD><TD>20ms</TD></TR>
                <TR><TD>0x130</TD><TD>PowerModeState</TD><TD>0-7</TD><TD>100ms</TD></TR>
                <TR><TD>0x210</TD><TD>CurrentGear</TD><TD>0-3</TD><TD>50ms</TD></TR>
                <TR><TD>0x310</TD><TD>WheelSpeed_FL</TD><TD>0-15</TD><TD>10ms</TD></TR>
                <TR><TD>0x510</TD><TD>IgnitionSwitch</TD><TD>0-2</TD><TD>100ms</TD></TR>
                </TABLE>
            >];
        }
    }
    """)
    dot_file = DIAGRAM_DIR / "can_bus_topology.dot"
    dot_file.write_text(dot)
    subprocess.run(
        ["dot", "-Tpng", "-Gdpi=150", str(dot_file), "-o", str(DIAGRAM_DIR / "can_bus_topology.png")],
        check=True,
    )
    dot_file.unlink()
    print("  Generated: can_bus_topology.png")


if __name__ == "__main__":
    DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating automotive engineering diagrams...")
    generate_pcm_state_machine()
    generate_shift_logic_flow()
    generate_can_topology()
    print("Done — diagrams written to", DIAGRAM_DIR)
