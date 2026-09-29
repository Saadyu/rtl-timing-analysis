import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

TIMING_FLOW = (
    PROJECT_ROOT
    / "scripts"
    / "timing_flow.py"
)

ANALYZE_TIMING = (
    PROJECT_ROOT
    / "scripts"
    / "analyze_timing.py"
)

SUMMARIZE_TIMING = (
    PROJECT_ROOT
    / "scripts"
    / "summarize_timing.py"
)


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
        "--clock-period",
        type=float,
        default=None,
        help="Single clock period in ns"
    )

    parser.add_argument(
        "--clock-periods",
        type=float,
        nargs="+",
        default=None,
        help="Clock periods to analyze in ns"
    )

    args = parser.parse_args()

    if (
        args.clock_period is not None
        and args.clock_periods is not None
    ):
        parser.error(
            "use either --clock-period "
            "or --clock-periods, not both"
        )

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

    return args


def run_command(command):

    print()
    print("=" * 70)
    print("RUNNING")
    print("=" * 70)
    print(" ".join(str(item) for item in command))
    print()

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Command failed with exit code "
            f"{result.returncode}"
        )


def main():

    args = parse_arguments()

    rtl_files = [
        rtl_file.resolve()
        for rtl_file in args.rtl
    ]
    sdc_file = args.sdc.resolve()

    for rtl_file in rtl_files:
        if not rtl_file.exists():
            raise FileNotFoundError(
                f"RTL file not found: {rtl_file}"
            )

    if not sdc_file.exists():
        raise FileNotFoundError(
            f"SDC file not found: {sdc_file}"
        )

    if not TIMING_FLOW.exists():
        raise FileNotFoundError(
            f"Timing flow script not found: "
            f"{TIMING_FLOW}"
        )

    if not ANALYZE_TIMING.exists():
        raise FileNotFoundError(
            f"Analysis script not found: "
            f"{ANALYZE_TIMING}"
        )

    if not SUMMARIZE_TIMING.exists():
        raise FileNotFoundError(
            f"Summary script not found: "
            f"{SUMMARIZE_TIMING}"
        )

    if args.clock_periods is not None:

        periods = args.clock_periods

    elif args.clock_period is not None:

        periods = [args.clock_period]

    else:

        periods = [2.0, 4.0]

    for period in periods:

        command = [
            sys.executable,
            str(TIMING_FLOW),
            "--rtl",
        ]

        command.extend(
            str(rtl_file)
            for rtl_file in rtl_files
        )

        command.extend([
            "--top",
            args.top,
            "--sdc",
            str(sdc_file),
        ])
        if period is not None:
            command.extend([
                "--clock-period",
                str(period)
            ])

        run_command(command)

    design_name = args.top

    run_command([
        sys.executable,
        str(ANALYZE_TIMING),
        "--design",
        design_name
    ])

    run_command([
        sys.executable,
        str(SUMMARIZE_TIMING),
        "--design",
        design_name
    ])


if __name__ == "__main__":
    main()