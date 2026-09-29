import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
OUTPUT_DIR = PROJECT_ROOT / "reports"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Analyze RTL timing results"
    )

    parser.add_argument(
        "--design",
        type=str,
        required=True,
        help="Design name to analyze"
    )

    return parser.parse_args()


def read_timing_csv(csv_file):
    with csv_file.open(newline="") as f:
        return list(csv.DictReader(f))


def main():

    args = parse_arguments()

    design_dir = RESULTS_DIR / args.design

    if not design_dir.exists():
        raise FileNotFoundError(
            f"Results directory not found: {design_dir}"
        )

    csv_files = sorted(
        csv_file
        for csv_file in design_dir.glob("*/timing_reports.csv")
        if csv_file.parent.name != "sdc_default"
    )

    if not csv_files:
        raise RuntimeError(
            f"No timing results found for design: {args.design}"
        )

    rows = []

    for csv_file in csv_files:

        file_rows = read_timing_csv(
            csv_file
        )

        if not file_rows:
            raise RuntimeError(
                f"Timing result file is empty: "
                f"{csv_file}"
            )

        for row in file_rows:

            if not row.get("clock_period_ns"):
                raise RuntimeError(
                    "Missing clock period in timing result: "
                    f"{csv_file}"
                )

            rows.append(row)

    if not rows:
        raise RuntimeError(
            "Timing result files are empty."
        )

    design_report_dir = (
        OUTPUT_DIR
        / args.design
    )

    design_report_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        design_report_dir
        / "timing_analysis.csv"
    )

    fieldnames = [
        "corner",
        "library",
        "process",
        "clock_period_ns",
        "slack_ns",
        "tns_ns",
        "status",
        "startpoint",
        "endpoint"        
    ]

    with output_file.open(
        "w",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for row in rows:
            writer.writerow({
                field: row.get(field, "")
                for field in fieldnames
            })

    periods = sorted(
        set(
            row["clock_period_ns"]
            for row in rows
        )
    )

    print()
    print("=" * 70)
    print("TIMING ANALYSIS GENERATED")
    print("=" * 70)
    print(f"Design     : {args.design}")
    print(f"Input runs : {len(periods)}")
    print(f"Data rows  : {len(rows)}")
    print(f"Output     : {output_file}")


if __name__ == "__main__":
    main()
