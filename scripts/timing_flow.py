#!/usr/bin/env python3

import subprocess
import argparse
import csv
import re
import os
import shutil
import importlib.util
from pathlib import Path

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = PROJECT_ROOT / "results"

YOSYS = "yosys"
STA = "sta"

DEFAULT_CONFIG = (
    PROJECT_ROOT
    / "configs"
    / "sky130.py"
)

# ============================================================
# LOAD TECHNOLOGY CONFIGURATION
# ============================================================

def load_config(config_file):

    config_file = Path(config_file).resolve()

    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_file}"
        )

    spec = importlib.util.spec_from_file_location(
        "timing_config",
        config_file
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Could not load configuration: {config_file}"
        )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    if not hasattr(module, "CORNERS"):
        raise RuntimeError(
            f"Configuration does not define CORNERS: "
            f"{config_file}"
        )

    return module.CORNERS

# ============================================================
# RUN COMMAND
# ============================================================

def run_command(command, log_file=None):

    print()
    print("=" * 70)
    print("Running:")
    print(" ".join(str(x) for x in command))
    print("=" * 70)

    if log_file is not None:

        log_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(log_file, "w") as log:

            result = subprocess.run(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True
            )

    else:

        result = subprocess.run(
            command,
            text=True
        )

    if result.returncode != 0:

        raise RuntimeError(
            "Command failed with return code "
            + str(result.returncode)
        )

    if log_file is not None:

        print()
        print("Command completed successfully.")
        print("Log saved to:", log_file)

    return ""



# ============================================================
# PARSE WORST SLACK
# ============================================================

def parse_worst_slack(text):

    match = re.search(
        r"worst\s+slack\s+max\s+"
        r"([-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    return float(match.group(1))

def parse_tns(text):
    match = re.search(
        r"tns\s+max\s+"
        r"([-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))",
        text,
        re.IGNORECASE
    )
    if not match:
        return None
    return float(match.group(1))

def parse_worst_path(text):

    startpoint_match = re.search(
        r"Startpoint:\s+(.+)",
        text
    )

    endpoint_match = re.search(
        r"Endpoint:\s+(.+)",
        text
    )

    startpoint = (
        startpoint_match.group(1).strip()
        if startpoint_match
        else None
    )

    endpoint = (
        endpoint_match.group(1).strip()
        if endpoint_match
        else None
    )

    return startpoint, endpoint

# ============================================================
# DETERMINE TIMING STATUS
# ============================================================

def determine_status(slack):

    if slack is None:

        return "UNKNOWN"

    if slack >= 0:

        return "MET"

    return "VIOLATED"


# ============================================================
# CREATE YOSYS SCRIPT
# ============================================================

def create_yosys_script(
    liberty,
    corner,
    output_dir,
    rtl_files,
    top_module
):

    output_netlist = (
        output_dir
        / "synth"
        / f"{top_module}_{corner}_synth.v"
    )

    script_file = (
        output_dir
        / "yosys"
        / f"yosys_{corner}.ys"
    )

    output_netlist.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    script_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    rtl_commands = "\n".join(
        f"read_verilog -sv {rtl_file}"
        for rtl_file in rtl_files
    )

    script = "\n".join([

        "# ============================================================",
        "# Yosys synthesis",
        f"# Corner: {corner}",
        f"# Liberty: {liberty}",
        "# ============================================================",
        "",

        f"read_liberty -lib {liberty}",
        "",

        f"{rtl_commands}",
        "",

        f"hierarchy -check -top {top_module}",
        "",

        f"synth -top {top_module}",

        "flatten",

        "opt",
        
        "",

        f"dfflibmap -liberty {liberty}",
        
        "",

        "opt",
        
        "",

        f"abc -liberty {liberty}",
        "",

        "opt",
        "clean",
        "",

        f"write_verilog -noattr {output_netlist}",
        "",
    ])

    script_file.write_text(script)

    return script_file, output_netlist

def get_output_dir(
    clock_period,
    results_root,
    design_name
):
    if clock_period is None:
        clock_tag = "sdc_default"
    else:
        clock_tag = f"{clock_period:g}ns"

    return (
        results_root
        / design_name
        / clock_tag
    )

def create_run_sdc(clock_period, output_dir, base_sdc_file):

    if clock_period is None:
        return base_sdc_file

    if not base_sdc_file.exists():
        raise FileNotFoundError(
            f"Base SDC file not found: {base_sdc_file}"
        )

    run_sdc = (
        output_dir
        / "constraints"
        / f"{base_sdc_file.stem}.sdc"
    )

    run_sdc.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    sdc_text = base_sdc_file.read_text()

    pattern = (
        r"(create_clock\s+"
        r"(?:-name\s+\S+\s+)?"
        r"-period\s+)"
        r"[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)"
    )

    replacement = rf"\g<1>{clock_period:g}"

    modified_sdc, count = re.subn(
        pattern,
        replacement,
        sdc_text,
        count=1,
        flags=re.IGNORECASE
    )

    if count != 1:
        raise RuntimeError(
            "Could not find a create_clock "
            "constraint in the base SDC."
        )

    run_sdc.write_text(
        modified_sdc
    )

    return run_sdc

# ============================================================
# CREATE OPENSTA SCRIPT
# ============================================================

def create_sta_script(
    liberty,
    netlist,
    corner,
    sdc_file,
    output_dir,
    top_module
):

    sta_file = (
        output_dir
        / "sta"
        / f"sta_{corner}.tcl"
    )

    sta_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    timing_report = (
        output_dir
        / "timing"
        / f"timing_{corner}.rpt"
    )

    timing_report.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    sta_script = f"""
read_liberty {liberty}
read_verilog {netlist}
link_design {top_module}
read_sdc {sdc_file}

report_checks -path_delay max -fields {{slew cap input_pins startpoint endpoint}} > {timing_report}
report_worst_slack -max
report_tns

exit
"""

    sta_file.write_text(sta_script)

    return sta_file, timing_report

# ============================================================
# RUN ONE CORNER
# ============================================================

def run_corner(
    corner,
    config,
    sdc_file,
    output_dir,
    clock_period,
    rtl_files,
    top_module
):

    print()
    print("#" * 70)
    print(f"# ANALYZING CORNER: {corner}")
    print("#" * 70)

    # --------------------------------------------------------
    # Get Liberty
    # --------------------------------------------------------

    liberty = config.get("liberty")

    if liberty is not None:
        liberty = Path(liberty)

    if liberty is None or not liberty.is_file():

        print(
            f"ERROR: Could not find Liberty for {corner}"
        )

        return {
            "corner": corner,
            "library": config["library"],
            "process": config["process"],
            "clock_period_ns": clock_period,
            "liberty": "NOT FOUND",
            "slack_ns": "",
            "tns_ns": "",
            "status": "LIBRARY NOT FOUND",
            "startpoint": "",
            "endpoint": "",
        }

    print("Liberty found:")
    print(liberty)

    # --------------------------------------------------------
    # Create Yosys script
    # --------------------------------------------------------

    yosys_script, netlist = create_yosys_script(
    liberty,
    corner,
    output_dir,
    rtl_files,
    top_module
)

    # --------------------------------------------------------
    # Run Yosys
    # --------------------------------------------------------

    yosys_log = (
        output_dir
        / "logs" / "yosys"
        / f"yosys_{corner}.log"
    )

    try:

        run_command(
            [
                YOSYS,
                "-s",
                str(yosys_script)
            ],
            log_file=yosys_log
        )

    except RuntimeError as error:

        print(f"ERROR: Yosys failed for {corner}")
        print(error)

        return {
            "corner": corner,
            "library": config["library"],
            "process": config["process"],
            "clock_period_ns": clock_period,
            "liberty": str(liberty),
            "slack_ns": "",
            "tns_ns": "",
            "status": "YOSYS FAILED",
            "startpoint": "",
            "endpoint": "",
        }

    # --------------------------------------------------------
    # Create OpenSTA script
    # --------------------------------------------------------

    sta_script, report_file = create_sta_script(
        liberty,
        netlist,
        corner,
        sdc_file,
        output_dir,
        top_module
    )

    # --------------------------------------------------------
    # Run OpenSTA
    # --------------------------------------------------------

    sta_log = (
        output_dir
        / "logs" / "sta"
        / f"sta_{corner}.log"
    )

    try:

        run_command(
            [
                STA,
                str(sta_script)
            ],
            log_file=sta_log
        )

        sta_output = sta_log.read_text()
        timing_output = report_file.read_text()

    except RuntimeError as error:

        print(f"ERROR: OpenSTA failed for {corner}")
        print(error)

        return {
            "corner": corner,
            "library": config["library"],
            "process": config["process"],
            "clock_period_ns": clock_period,
            "liberty": str(liberty),
            "slack_ns": "",
            "tns_ns": "",
            "status": "STA FAILED",
            "startpoint": "",
            "endpoint": "",
        }

    # --------------------------------------------------------
    # Parse timing result
    # --------------------------------------------------------

    slack = parse_worst_slack(
        sta_output
    )

    tns = parse_tns(
        sta_output
    )

    startpoint, endpoint = parse_worst_path(
        timing_output
    )

    status = determine_status(
        slack
    )

    return {
        "corner": corner,
        "clock_period_ns": clock_period,
        "library": config["library"],
        "process": config["process"],
        "liberty": str(liberty),
        "slack_ns": (
            ""
            if slack is None
            else slack
        ),
        "tns_ns": (
            ""
            if tns is None
            else tns
        ),
        "status": status,
        "startpoint": (
            ""
            if startpoint is None
            else startpoint
        ),
        "endpoint": (
            ""
            if endpoint is None
            else endpoint
        ),
    }


# ============================================================
# WRITE CSV
# ============================================================

def write_csv(results, output_dir):

    csv_file = (
        output_dir
        / "timing_reports.csv"
    )

    with csv_file.open(
        "w",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "corner",
                "library",
                "process",
                "clock_period_ns",
                "liberty",
                "slack_ns",
                "tns_ns",
                "status",
                "startpoint",
                "endpoint"
            ]
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    return csv_file

def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Generic RTL timing analysis flow"
    )

    parser.add_argument(
        "--rtl",
        type=Path,
        nargs="+",
        required=True,
        help="RTL/SystemVerilog source file(s)"
    )

    parser.add_argument(
        "--top",
        type=str,
        required=True,
        help="Top-level RTL module"
    )

    parser.add_argument(
        "--sdc",
        type=Path,
        required=True,
        help="SDC constraints file"
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Technology configuration file"
    )

    parser.add_argument(
        "--clock-period",
        type=float,
        default=None,
        help="Optional clock period override in ns"
    )

    parser.add_argument(
        "--clock-periods",
        type=float,
        nargs="+",
        default=None,
        help="Optional list of clock periods to analyze in ns"
    )

    args = parser.parse_args()

    if args.clock_period is not None:
        if args.clock_period <= 0:
            parser.error(
                "clock period must be greater than 0"
            )

    if args.clock_periods is not None:
        if any(
            period <= 0
            for period in args.clock_periods
        ):
            parser.error(
                "all clock periods must be greater than 0"
            )

    if (
        args.clock_period is not None
        and args.clock_periods is not None
    ):
        parser.error(
            "use either --clock-period "
            "or --clock-periods, not both"
        )

    return args

# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(results):

    print()
    print("=" * 90)
    print("FINAL PVT TIMING SUMMARY")
    print("=" * 90)

    print(
        "{:<12}{:<22}{:<10}{:<15}{:<15}".format(
            "Corner",
            "Library",
            "Process",
            "Slack(ns)",
            "Status"
        )
    )

    print("-" * 90)

    for result in results:

        print(
            "{:<12}{:<22}{:<10}{:<15}{:<15}".format(
                result["corner"],
                result["library"],
                result["process"],
                str(result["slack_ns"]),
                result["status"]
            )
        )

    print("=" * 90)

def get_clock_periods(args):

    if args.clock_periods is not None:
        return args.clock_periods

    if args.clock_period is not None:
        return [args.clock_period]

    return [None]

def get_design_name(rtl_file, top_module):
    if top_module:
        return top_module
    return rtl_file.stem

# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_arguments()

    corners = load_config(
        args.config
    )

    rtl_files = [
        rtl_file.resolve()
        for rtl_file in args.rtl
    ]
    base_sdc_file = args.sdc.resolve()
    top_module = args.top

    design_name = get_design_name(
        rtl_files[0],
        top_module
    )

    results_root = PROJECT_ROOT / "results"

    for rtl_file in rtl_files:

        if not rtl_file.exists():
            raise FileNotFoundError(
                f"RTL file not found: {rtl_file}"
            )

    if not base_sdc_file.exists():
        raise FileNotFoundError(
            f"SDC file not found: {base_sdc_file}"
        )


    clock_periods = get_clock_periods(args)

    for clock_period in clock_periods:

        output_dir = get_output_dir(
            clock_period,
            results_root,
            design_name
        )

        if output_dir.exists():
            shutil.rmtree(output_dir)

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        sdc_file = create_run_sdc(
            clock_period,
            output_dir,
            base_sdc_file
        )

        print()
        print("=" * 70)

        if clock_period is None:
            print("Clock period : SDC default")
        else:
            print(
                f"Clock period : {clock_period} ns"
            )

        print(
            f"Output       : {output_dir}"
        )

        print("=" * 70)

        results = []

        for corner, config in corners.items():
            result = run_corner(
            corner,
            config,
            sdc_file,
            output_dir,
            clock_period,
            rtl_files,
            top_module
        )

            results.append(result)

        csv_file = write_csv(
            results,
            output_dir
        )

        print_summary(
            results
        )

        print()
        print("Results saved to:")
        print(csv_file)


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    main()