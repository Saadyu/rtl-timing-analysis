# RTL Timing Analysis Framework

A reusable RTL timing-analysis framework using **Yosys** for synthesis and **OpenSTA** for static timing analysis.

The framework is designed to work with different RTL designs and different standard-cell libraries. Technology-specific information is kept in configuration files rather than being built into the timing engine.

---

## Features

* SystemVerilog / Verilog RTL support
* Multiple RTL source files
* Configurable top-level module
* SDC timing constraints
* Multiple standard-cell libraries
* Multiple PVT/corner configurations
* Arbitrary Liberty (`.lib`) file locations
* Sky130 automatic library discovery
* Multiple clock-period analysis
* Timing reports from OpenSTA
* Worst slack and TNS analysis
* Per-clock-period summaries
* Fmax calculation when multiple clock periods are analyzed
* Clean handling of failed library configurations

---

## Project Structure

```text
rtl-timing-analysis/
├── .gitignore
├── README.md
│
├── examples/
│   ├── alu_8.sv
│   ├── alu_8.sdc
│   ├── alu_8_test.v
│   ├── counter.sv
│   ├── counter.sdc
│   ├── adder.sv
│   ├── multi_top.sv
│   └── multi_top.sdc
│
├── scripts/
│   ├── timing_flow.py
│   ├── analyze_timing.py
│   └── summarize_timing.py
│
├── configs/
│   ├── sky130.py
│   └── example.py
│
├── run.py
│
├── results/       # generated timing data
└── reports/       # generated analysis reports
```

`results/` and `reports/` are generated automatically and are ignored by Git.

---

# 1. Requirements

Install the following tools:

* Python 3
* Yosys
* OpenSTA

Verify the installations:

```bash
python3 --version
yosys -V
sta -version
```

The framework calls `yosys` and `sta` from the system `PATH`.

---

# 2. Clone the Repository

Clone the repository:

```bash
git clone https://github.com/Saadyu/rtl-timing-analysis.git
cd rtl-timing-analysis
```

---

# 3. Provide RTL

Place your RTL source files in a convenient location.

For example:

```text
examples/
└── alu_8.sv
```

A design may contain multiple RTL files.

Example:

```bash
python3 run.py \
    --rtl examples/module_a.sv examples/module_b.sv \
    --top my_top \
    --sdc examples/my_top.sdc
```

The `--top` argument must identify the top-level RTL module.

---

# 4. Provide an SDC File

The framework uses an SDC file to define timing constraints.

For example:

```tcl
create_clock -name clk -period 2.0 [get_ports clk]

set_input_delay -clock clk 0 [get_ports {a b opcode}]

set_output_delay -clock clk 0 [get_ports {y carry}]
```

Example file:

```text
examples/alu_8.sdc
```

The SDC file is passed using:

```bash
--sdc examples/alu_8.sdc
```

---

# 5. Configure the Standard-Cell Library

This framework does not require a particular standard-cell library directory structure.

The important requirement is that you have compatible Liberty files and provide their paths through a configuration file.

There are two configuration approaches.

---

## Option A: Generic Library Configuration

Use this approach when working with an arbitrary standard-cell library.

Start with:

```text
configs/example.py
```

A configuration looks like:

```python
from pathlib import Path


CORNERS = {

    "typical": {
        "library": "my_library",
        "process": "tt",
        "liberty": Path(
            "/path/to/typical.lib"
        ),
    },

    "slow": {
        "library": "my_library",
        "process": "ss",
        "liberty": Path(
            "/path/to/slow.lib"
        ),
    },

    "fast": {
        "library": "my_library",
        "process": "ff",
        "liberty": Path(
            "/path/to/fast.lib"
        ),
    },

}
```

The paths can point to Liberty files anywhere on the system.

The framework does **not** require:

```text
share/pdk/
libs.ref/
```

or any other particular directory structure.

It also does not require the corners to be named `tt`, `ss`, and `ff`. Those names are simply examples.

For example, a library could instead define:

```python
CORNERS = {

    "nominal": {
        "library": "my_cells",
        "process": "nominal",
        "liberty": Path("/libs/nominal.lib"),
    },

    "hot": {
        "library": "my_cells",
        "process": "hot",
        "liberty": Path("/libs/hot.lib"),
    },

}
```

The number of corners is also configurable.

---

# 6. Sky130 Configuration

For Sky130, the repository includes:

```text
configs/sky130.py
```

This configuration understands the Sky130 PDK directory structure and automatically discovers compatible Liberty files.

If the Sky130 PDK is installed and `PDK_ROOT` is configured, the default configuration can be used without specifying `--config`.

For example:

```bash
python3 run.py \
    --rtl examples/alu_8.sv \
    --top alu_8 \
    --sdc examples/alu_8.sdc
```

The Sky130 configuration is a convenience configuration. The timing engine itself is not tied to Sky130.

---

# 7. Run Timing Analysis

Basic command:

```bash
python3 run.py \
    --rtl examples/alu_8.sv \
    --top alu_8 \
    --sdc examples/alu_8.sdc \
    --config configs/example.py
```

When no clock-period option is supplied, the framework analyzes its default clock periods.

---

# 8. Analyze a Single Clock Period

Use:

```bash
python3 run.py \
    --rtl examples/alu_8.sv \
    --top alu_8 \
    --sdc examples/alu_8.sdc \
    --config configs/example.py \
    --clock-period 2
```

This analyzes the design at a 2 ns clock period.

---

# 9. Analyze Multiple Clock Periods

To explicitly select the periods:

```bash
python3 run.py \
    --rtl examples/alu_8.sv \
    --top alu_8 \
    --sdc examples/alu_8.sdc \
    --config configs/example.py \
    --clock-periods 2 3 4 5 8
```

Multiple periods allow the framework to analyze timing behavior across different clock requirements.

They also allow Fmax to be calculated.

---

# 10. Understanding the Results

Generated results are stored under:

```text
results/<design>/
```

For example:

```text
results/
└── alu_8/
    ├── 2ns/
    └── 4ns/
```

Each run contains generated Yosys scripts, synthesized netlists, OpenSTA scripts, logs, and timing reports.

The higher-level analysis is stored under:

```text
reports/<design>/
```

For example:

```text
reports/
└── alu_8/
    ├── timing_analysis.csv
    └── timing_summary.txt
```

---

# 11. Timing Summary

The final summary includes:

* Worst slack
* Worst TNS
* Timing status
* Number of passing corners
* Number of violating corners
* Results for each clock period
* Fmax when multiple periods are available

Example:

```text
Worst Slack
----------------------------------------------------------------------
Clock period : 2.0 ns
Corner       : slow
Slack        : -5.79 ns

Worst TNS
----------------------------------------------------------------------
Clock period : 2.0 ns
Corner       : slow
TNS          : -26.11 ns

Timing Status
----------------------------------------------------------------------
MET          : 3
VIOLATED     : 3
TOTAL        : 6
```

A negative slack indicates a timing violation for that analyzed constraint.

---

# 12. Fmax Analysis

When at least two clock periods are analyzed, the framework calculates a critical period and corresponding Fmax.

For example:

```text
Fmax Analysis
----------------------------------------------------------------------
STA periods used             : 2
Calculated critical period  : 7.79 ns
Calculated Fmax             : 128.37 MHz
```

If only one clock period is analyzed, Fmax is not calculated because there are not enough timing points for the framework's current Fmax analysis.

---

# 13. Failed Library Configurations

If a Liberty file cannot be found, the framework reports:

```text
ERROR: Could not find Liberty for typical
```

and records:

```text
LIBRARY NOT FOUND
```

The remaining corners can still be processed.

If all configured corners fail, the framework exits cleanly and reports:

```text
No valid timing results were found.

All analyzed corners failed before timing analysis could be performed.
```

This prevents stale results from previous runs from being mistaken for results from the current configuration.

---

# 14. Main Components

### `run.py`

Top-level entry point.

It:

1. Validates inputs.
2. Selects clock periods.
3. Runs the timing engine.
4. Runs timing analysis.
5. Generates the final summary.

### `scripts/timing_flow.py`

Technology-independent timing engine.

It:

1. Loads the selected configuration.
2. Reads the RTL.
3. Synthesizes the design using Yosys.
4. Generates the OpenSTA input.
5. Runs OpenSTA.
6. Extracts timing results.

### `scripts/analyze_timing.py`

Collects timing results from generated runs and produces:

```text
timing_analysis.csv
```

### `scripts/summarize_timing.py`

Processes the analyzed timing data and generates:

```text
timing_summary.txt
```

### `configs/sky130.py`

Sky130-specific configuration and Liberty discovery.

### `configs/example.py`

Generic configuration template for arbitrary standard-cell libraries.

---

# 15. Using a Different Standard-Cell Library

For a new library:

1. Obtain the Liberty files.
2. Copy `configs/example.py`.
3. Change the Liberty paths.
4. Define the corners you want to analyze.
5. Run `run.py` with that configuration.

For example:

```bash
cp configs/example.py configs/my_library.py
```

Edit:

```text
configs/my_library.py
```

Then run:

```bash
python3 run.py \
    --rtl my_design.sv \
    --top my_design \
    --sdc my_design.sdc \
    --config configs/my_library.py
```

No changes to `scripts/timing_flow.py` are required simply because the standard-cell library is different.

---

# 16. Design Independence

The timing engine is intended to be reusable across different RTL designs.

The user supplies:

```text
RTL
 │
 ├── top module
 │
 ├── SDC constraints
 │
 └── standard-cell Liberty configuration
```

The framework then performs:

```text
RTL
 ↓
Yosys synthesis
 ↓
Technology-mapped netlist
 ↓
OpenSTA
 ↓
Timing reports
 ↓
Timing analysis
 ↓
Summary / Fmax
```

The technology-specific information belongs in the configuration file rather than in the timing engine.

---

# 17. Example

For the included 8-bit ALU:

```bash
python3 run.py \
    --rtl examples/alu_8.sv \
    --top alu_8 \
    --sdc examples/alu_8.sdc \
    --config configs/example.py \
    --clock-periods 2 4
```

The resulting reports can be found under:

```text
reports/alu_8/
```

and detailed generated timing data under:

```text
results/alu_8/
```

---

## License

Add the project's license information here when a license is selected.
