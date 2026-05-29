# CAN Signal Catalog — Vehicle Network

**Document ID:** ES-CAN-2024-003  
**Revision:** A  
**Bus Configuration:** HS-CAN (500 kbps) + MS-CAN (125 kbps)

---

## 1. Network Topology

> **See Figure 1:** `../pdf_specs/diagrams/can_bus_topology.png`

The vehicle CAN network consists of two buses bridged by a gateway ECU.
The High-Speed CAN (HS-CAN) carries powertrain, chassis, and safety-critical
signals at 500 kbps. The Medium-Speed CAN (MS-CAN) carries body, climate,
and infotainment signals at 125 kbps.

## 2. HS-CAN Message Definitions

### 2.1 PCM Engine Status (0x120)
- Cycle time: 10 ms
- DLC: 8 bytes
- Signals: EngineRPM, EngineTorque, ThrottlePosition, EngineTemp

### 2.2 PCM Vehicle Speed (0x121)
- Cycle time: 20 ms
- DLC: 8 bytes
- Signals: VehicleSpeed, OutputShaftSpeed

### 2.3 PCM Power Mode (0x130)
- Cycle time: 100 ms
- DLC: 4 bytes
- Signals: PowerModeState, StarterRelay, FuelPumpRelay, IgnitionCoilEn

### 2.4 TCM Gear Status (0x210)
- Cycle time: 50 ms
- DLC: 8 bytes
- Signals: CurrentGear, TransRange, ShiftInProgress, TorqueConverterLocked, TransFluidTemp

### 2.5 ABS Wheel Speed (0x310)
- Cycle time: 10 ms
- DLC: 8 bytes
- Signals: WheelSpeed_FL, WheelSpeed_FR, WheelSpeed_RL, WheelSpeed_RR

### 2.6 BCM Ignition (0x510)
- Cycle time: 100 ms
- DLC: 4 bytes
- Signals: IgnitionSwitch, StartRequest, BrakePedal
