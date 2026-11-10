import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

from .core import analyze, hardware, load_iq, spectrogram


def main(argv=None):
    parser = argparse.ArgumentParser(prog="spectrumlens")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("hardware")
    run = sub.add_parser("analyze")
    run.add_argument("input", type=Path)
    run.add_argument("--format", choices=["cf32le", "cs16le"], required=True)
    run.add_argument("--sample-rate", type=float, required=True)
    run.add_argument("--center-hz", type=float, required=True)
    run.add_argument("--fft-size", type=int, default=1024)
    run.add_argument("--output", type=Path)
    run.add_argument("--csv", type=Path)
    run.add_argument("--png", type=Path)
    run.add_argument("--waterfall", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "hardware":
            print(json.dumps(hardware(), indent=2))
            return 0
        samples = load_iq(args.input, args.format)
        report = analyze(samples, args.sample_rate, args.center_hz, args.fft_size)
        report.update({"source_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(), "sample_format": args.format})
        if args.waterfall:
            report["spectrogram"] = spectrogram(samples, args.sample_rate, args.fft_size)
        if args.csv:
            with args.csv.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["frequency_hz", "psd_db_per_hz"])
                writer.writerows(zip(report["frequency_hz"], report["psd_db_per_hz"]))
        if args.png:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            ax.plot(report["frequency_hz"], report["psd_db_per_hz"])
            ax.set(xlabel="Frequency (Hz)", ylabel="Relative PSD (dB/Hz)")
            fig.savefig(args.png)
            plt.close(fig)
        result = json.dumps(report) + "\n"
        if args.output:
            args.output.write_text(result)
        else:
            print(result, end="")
        return 0
    except (OSError, ValueError, ImportError) as exc:
        print(f"spectrumlens: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
