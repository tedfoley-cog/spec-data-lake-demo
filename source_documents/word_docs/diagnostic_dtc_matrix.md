# Diagnostic Trouble Code Matrix

**Document ID:** ES-DTC-2024-004  
**Revision:** B  
**Scope:** Powertrain, Transmission, Network, and Emissions DTCs

---

## 1. Scope

This document defines all diagnostic trouble codes (DTCs) for the powertrain
and transmission control modules. Each DTC includes enable conditions,
debounce criteria, fault actions, and cross-references to requirements and
CAN signals.

## 2. DTC Summary Table

| DTC | Description | Category | Enable Condition | Fault Action | MIL |
|-----|-------------|----------|-----------------|--------------|-----|
| P0335 | Crankshaft Position Sensor — No Signal | Powertrain | Engine running, RPM absent 5s | Limit torque 80% | Yes |
| P0562 | System Voltage Low | Electrical | Any mode, V < 9.0V for 30s | Disable non-essential loads | Yes |
| P0563 | System Voltage High | Electrical | Any mode, V > 16.0V for 10s | Reduce alternator duty | Yes |
| P0602 | PCM Calibration Error | Powertrain | POST checksum mismatch | Enter limp mode | Yes |
| P0700 | Transmission Control Malfunction | Transmission | Shift rejected | Inhibit shift attempts | Yes |
| P0705 | Trans Range Sensor Circuit | Transmission | Sensor conflict | Default to Park interlock | Yes |
| P0730 | Incorrect Gear Ratio | Transmission | Ratio deviation > 15% | Limit to 3rd gear | Yes |
| U0100 | Lost Communication with ECM | Network | No CAN msg for 1s | Use last known values | Yes |
| U0073 | Control Module Comm Bus Off | Network | Error counter > 255 | Attempt bus recovery | Yes |
| P1000 | OBD Monitor Not Complete | Emissions | Monitors incomplete | Informational | No |

## 3. Cross-Reference Matrix

| DTC | Related Signal | Related Requirement |
|-----|---------------|-------------------|
| P0335 | EngineRPM | REQ-PM-001 |
| P0562 | BatteryVoltage | REQ-PM-002 |
| P0563 | BatteryVoltage | REQ-PM-003 |
| P0602 | PowerModeState | REQ-PM-004 |
| P0700 | CurrentGear | REQ-TR-009 |
| P0705 | TransRange | REQ-TR-010 |
| P0730 | CurrentGear | REQ-TR-011 |
| U0100 | EngineRPM | REQ-NET-001 |
| U0073 | PowerModeState | REQ-NET-002 |
| P1000 | PowerModeState | REQ-EM-001 |
