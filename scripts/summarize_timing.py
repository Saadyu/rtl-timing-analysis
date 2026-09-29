import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
SUMMARY_DIR = REPORTS_DIR

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Summarize RTL timing analysis"
    )

    parser.add_argument(
        "--design",
        type=str,
        required=True,
        help="Design name to summarize"
    )

    return parser.parse_args()


def load_results(input_file):

    with input_file.open(newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise RuntimeError(
            f"No timing results found in {input_file}"
        )

    valid_rows = []

    for row in rows:

        row["clock_period_ns"] = float(
            row["clock_period_ns"]
        )

        if row["status"] not in {
            "MET",
            "VIOLATED",
        }:
            continue

        row["slack_ns"] = float(
            row["slack_ns"]
        )

        row["tns_ns"] = float(
            row["tns_ns"]
        )

        valid_rows.append(row)

    return valid_rows


def analyze_fmax(rows):

    periods = sorted(
        set(
            row["clock_period_ns"]
            for row in rows
        )
    )

    if len(periods) < 2:
        return None

    critical_delays = []

    for period in periods:

        period_rows = [
            row
            for row in rows
            if row["clock_period_ns"] == period
        ]

        for row in period_rows:

            critical_delay = (
                row["clock_period_ns"]
                - row["slack_ns"]
            )

            critical_delays.append(
                critical_delay
            )

    critical_period = max(
        critical_delays
    )

    fmax_mhz = (
        1000.0
        / critical_period
    )

    return {
        "critical_period_ns": critical_period,
        "fmax_mhz": fmax_mhz,
        "num_periods": len(periods),
    }

def main():

    args = parse_arguments()

    design_report_dir = (
        REPORTS_DIR
        / args.design
    )

    input_file = (
        design_report_dir
        / "timing_analysis.csv"
    )

    if not input_file.exists():
        raise FileNotFoundError(
            f"Timing analysis file not found: "
            f"{input_file}"
        )

    rows = load_results(
        input_file
    )

    if not rows:

        report = []

        report.append("=" * 70)
        report.append("TIMING ANALYSIS SUMMARY")
        report.append("=" * 70)
        report.append("")
        report.append(
            f"Design : {args.design}"
        )
        report.append("")
        report.append(
            "No valid timing results were found."
        )
        report.append("")
        report.append(
            "All analyzed corners failed before "
            "timing analysis could be performed."
        )
        report.append("")
        report.append(
            "Check the timing analysis CSV for "
            "the failure status of each corner."
        )

        report_text = "\n".join(report)

        print()
        print(report_text)

        SUMMARY_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        summary_file = (
            design_report_dir
            / "timing_summary.txt"
        )

        summary_file.write_text(
            report_text + "\n"
        )

        return

    worst_slack = min(
        rows,
        key=lambda row: row["slack_ns"]
    )

    worst_tns = min(
        rows,
        key=lambda row: row["tns_ns"]
    )

    met = sum(
        row["status"] == "MET"
        for row in rows
    )

    violated = sum(
        row["status"] == "VIOLATED"
        for row in rows
    )

    periods = sorted(
        set(
            row["clock_period_ns"]
            for row in rows
        )
    )

    fmax_result = analyze_fmax(rows)

    report = []

    report.append("=" * 70)
    report.append("TIMING ANALYSIS SUMMARY")
    report.append("=" * 70)
    report.append("")

    report.append(
        f"Design : {args.design}"
    )

    report.append("")
    report.append("Worst Slack")
    report.append("-" * 70)

    report.append(
        f"Clock period : "
        f"{worst_slack['clock_period_ns']} ns"
    )

    report.append(
        f"Corner       : "
        f"{worst_slack['corner']}"
    )

    report.append(
        f"Slack        : "
        f"{worst_slack['slack_ns']} ns"
    )

    report.append(
        f"Startpoint   : "
        f"{worst_slack['startpoint']}"
    )

    report.append(
        f"Endpoint     : "
        f"{worst_slack['endpoint']}"
    )

    report.append("")
    report.append("Worst TNS")
    report.append("-" * 70)

    report.append(
        f"Clock period : "
        f"{worst_tns['clock_period_ns']} ns"
    )

    report.append(
        f"Corner       : "
        f"{worst_tns['corner']}"
    )

    report.append(
        f"TNS          : "
        f"{worst_tns['tns_ns']} ns"
    )

    report.append("")
    report.append("Timing Status")
    report.append("-" * 70)

    report.append(
        f"MET          : {met}"
    )

    report.append(
        f"VIOLATED     : {violated}"
    )

    report.append(
        f"TOTAL        : {len(rows)}"
    )

    report.append("")
    report.append("Per Clock Period")
    report.append("-" * 70)

    for period in periods:

        period_rows = [
            row
            for row in rows
            if row["clock_period_ns"] == period
        ]

        period_worst_slack = min(
            period_rows,
            key=lambda row: row["slack_ns"]
        )

        period_worst_tns = min(
            period_rows,
            key=lambda row: row["tns_ns"]
        )

        period_violated = sum(
            row["status"] == "VIOLATED"
            for row in period_rows
        )

        report.append(
            f"{period:g} ns : "
            f"Worst Slack = "
            f"{period_worst_slack['slack_ns']:.2f} ns, "
            f"Worst TNS = "
            f"{period_worst_tns['tns_ns']:.2f} ns, "
            f"Violations = "
            f"{period_violated}/{len(period_rows)}"
        )

    report.append("")
    report.append("Fmax Analysis")
    report.append("-" * 70)

    if fmax_result is None:

        report.append(
            "At least two clock periods "
            "are required for Fmax calculation."
        )

    else:

        report.append(
            f"STA periods used             : "
            f"{fmax_result['num_periods']}"
        )

        report.append(
            f"Calculated critical period  : "
            f"{fmax_result['critical_period_ns']:.2f} ns"
        )

        report.append(
            f"Calculated Fmax             : "
            f"{fmax_result['fmax_mhz']:.2f} MHz"
        )

    report_text = "\n".join(report)

    print()
    print(report_text)

    SUMMARY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    summary_file = (
        design_report_dir
        / "timing_summary.txt"
    )

    summary_file.write_text(
        report_text + "\n"
    )

    print()
    print(
        f"Summary saved to : {summary_file}"
    )   
if __name__ == "__main__":
    main()