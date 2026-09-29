# Generic RTL Timing Analysis Framework

A reusable RTL timing-analysis framework using Yosys, OpenSTA, Sky130 standard-cell libraries, and Python 3.

## Project Structure

```text
alu_8/
├── rtl/
│   └── <user RTL files>
├── constraints/
│   └── <user SDC files>
├── examples/
│   └── <example designs>
├── scripts/
│   ├── timing_flow.py
│   ├── analyze_timing.py
│   └── summarize_timing.py
├── reports/
├── results/
└── run.py
```

Users should place their Verilog/SystemVerilog source files in `rtl/` and their SDC constraint files in `constraints/`.

Both `.sv` and `.v` RTL files are supported.

## Required Inputs

For each design, provide:

1. One or more RTL source files.
2. The name of the top-level RTL module.
3. An SDC constraints file.

For example:

```text
rtl/
├── cpu.sv
├── alu.sv
└── register_file.sv

constraints/
└── cpu.sdc
```

If the top-level module is:

```systemverilog
module cpu (...);
```

the top name is `cpu`.

A basic SDC clock constraint is:

```tcl
create_clock -name clk -period 5.0 [get_ports clk]
```

Add input/output timing constraints as required by the design.

## Running the Flow

The main entry point is:

```bash
python3 run.py
```

### Single RTL file

```bash
python3 run.py     --rtl rtl/cpu.sv     --top cpu     --sdc constraints/cpu.sdc
```

### Multiple RTL files

```bash
python3 run.py     --rtl rtl/cpu.sv rtl/alu.sv rtl/register_file.sv     --top cpu     --sdc constraints/cpu.sdc
```

The RTL files are synthesized together using the specified top-level module.

## Clock Periods

If no period option is supplied, the flow analyzes:

```text
2 ns
4 ns
```

### One specific period

```bash
python3 run.py     --rtl rtl/cpu.sv     --top cpu     --sdc constraints/cpu.sdc     --clock-period 5
```

### Multiple specific periods

```bash
python3 run.py     --rtl rtl/cpu.sv     --top cpu     --sdc constraints/cpu.sdc     --clock-periods 2 3 4 5 8
```

`--clock-period` and `--clock-periods` cannot be used together. All periods must be greater than zero.

## SDC Clock-Period Override

The supplied SDC is used as the base constraint file.

When a clock period is specified on the command line, the flow creates a run-specific SDC and replaces the period in the `create_clock` constraint. The original SDC is not modified.

For example:

```tcl
create_clock -name clk -period 5.0 [get_ports clk]
```

with:

```bash
--clock-period 2
```

produces a run-specific constraint using:

```tcl
create_clock -name clk -period 2 [get_ports clk]
```

## Synthesis and Timing Flow

For each configured timing corner, the framework performs:

```text
RTL
 ↓
Yosys hierarchy checking
 ↓
Synthesis
 ↓
Flattening
 ↓
Optimization
 ↓
DFF technology mapping
 ↓
ABC technology mapping
 ↓
Gate-level netlist
 ↓
OpenSTA
```

Multiple RTL source files are read together and synthesized using the specified top module.

## PVT Analysis

The current configuration analyzes Sky130 standard-cell library/process combinations using:

```text
Library families:
hs, hd, hdll, ms, ls, lp

Processes:
tt, ss, ff
```

The current configuration contains 17 valid PVT corners.

For each corner, the flow records:

- library
- process
- clock period
- worst slack
- total negative slack
- timing status
- worst startpoint
- worst endpoint

## Results

Intermediate timing-flow data is stored under:

```text
results/
```

Results are organized by design and clock period:

```text
results/
└── cpu/
    ├── 2ns/
    └── 4ns/
```

A repeated run for a particular design and clock period clears that period's existing result directory before generating new data. Other designs and other period directories are preserved.

## Reports

Processed reports are stored under:

```text
reports/
```

For example:

```text
reports/
└── cpu/
    ├── timing_analysis.csv
    └── timing_summary.txt
```

### timing_analysis.csv

Contains timing results for the analyzed PVT corners, including:

```text
corner
library
process
clock_period_ns
slack_ns
tns_ns
status
startpoint
endpoint
```

### timing_summary.txt

Contains a human-readable summary of:

- worst slack
- worst-slack corner
- worst timing-path startpoint and endpoint
- worst TNS
- number of MET corners
- number of violating corners
- timing results per clock period
- calculated Fmax when at least two periods are available

## Understanding Slack

```text
positive slack → timing requirement is met
zero slack     → timing requirement is exactly met
negative slack → timing violation
```

For example:

```text
Slack = +1.25 ns
```

means the path has 1.25 ns of timing margin.

```text
Slack = -2.50 ns
```

means the path violates the timing requirement by 2.50 ns.

## Understanding TNS

TNS means Total Negative Slack.

```text
TNS = 0
```

means there is no negative slack.

A negative TNS indicates that one or more timing paths violate their requirements.

## Fmax Calculation

When multiple clock periods are analyzed, the framework derives an estimated maximum operating frequency from the STA results.

For a timing result:

```text
Clock period = T
Slack = S
```

the implied critical path delay is:

```text
Critical delay = T - S
```

The corresponding frequency is:

```text
Fmax = 1000 / Critical delay
```

when the critical delay is in nanoseconds and Fmax is in MHz.

Example:

```text
Clock period = 4 ns
Worst slack  = -3.79 ns

Critical delay = 4 - (-3.79)
               = 7.79 ns

Fmax = 1000 / 7.79
     ≈ 128.37 MHz
```

This Fmax is calculated from the existing STA results and does not require an additional synthesis/STA run at the calculated critical period.

At least two analyzed clock periods are required by the reporting flow for Fmax calculation.

## Generic Workflow for a New Design

### 1. Add RTL

Put all source files in:

```text
rtl/
```

For example:

```text
rtl/
├── top.sv
├── datapath.sv
└── controller.sv
```

### 2. Add constraints

Put the SDC file in:

```text
constraints/
```

For example:

```text
constraints/top.sdc
```

### 3. Identify the top module

If the top-level module is:

```systemverilog
module top (...);
```

use:

```text
--top top
```

### 4. Run

```bash
python3 run.py     --rtl rtl/top.sv rtl/datapath.sv rtl/controller.sv     --top top     --sdc constraints/top.sdc
```

### 5. Inspect reports

```text
reports/top/timing_summary.txt
reports/top/timing_analysis.csv
```

## Design Requirements

The supplied design should have:

- synthesizable Verilog/SystemVerilog
- a valid top-level module
- valid module hierarchy
- an SDC file containing the required timing constraints
- a clock constraint for sequential timing analysis

The module specified with `--top` must exist in the supplied RTL files.

## Command Reference

### Default analysis

```bash
python3 run.py     --rtl rtl/<design>.sv     --top <top_module>     --sdc constraints/<design>.sdc
```

### Single period

```bash
python3 run.py     --rtl rtl/<design>.sv     --top <top_module>     --sdc constraints/<design>.sdc     --clock-period <period_ns>
```

### Multiple periods

```bash
python3 run.py     --rtl rtl/<design>.sv     --top <top_module>     --sdc constraints/<design>.sdc     --clock-periods <period1> <period2> <period3>
```

### Multiple RTL files

```bash
python3 run.py     --rtl rtl/file1.sv rtl/file2.sv rtl/file3.v     --top <top_module>     --sdc constraints/<design>.sdc
```

## Summary

The intended user workflow is:

```text
Put RTL in rtl/
        +
Put SDC in constraints/
        +
Specify the top module
        ↓
Run run.py
        ↓
Yosys synthesis + technology mapping
        ↓
OpenSTA PVT timing analysis
        ↓
CSV + human-readable reports
```

The Python scripts in `scripts/` implement the flow so that users normally do not need to modify them for each new RTL design.
