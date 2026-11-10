# SpectrumLens

SpectrumLens performs bounded receive-only spectrum analysis of offline complex IQ. It imports `cf32le` and `cs16le` interleaved samples, computes Welch PSD, a noise floor estimate, peaks, and an optional spectrogram; exports JSON, CSV, and PNG. Reported powers are relative digital sample levels, not calibrated dBm.

```sh
python3 -m spectrumlens.cli hardware
python3 -m spectrumlens.cli analyze authorized.iq --format cf32le --sample-rate 1000000 --center-hz 433920000 --waterfall --output report.json --csv psd.csv --png spectrum.png
```

IQ input is capped at 32 MB. Rates are validated between 1 kS/s and 20 MS/s and center frequencies between 100 kHz and 6 GHz as processing metadata, not as claimed device capability. See [ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY.md](SECURITY.md), [HARDWARE.md](HARDWARE.md), [DEPENDENCIES.md](DEPENDENCIES.md), and [VALIDATION_REPORT.md](VALIDATION_REPORT.md).
