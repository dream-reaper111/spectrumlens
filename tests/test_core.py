from pathlib import Path
import tempfile
import unittest

import numpy as np

from spectrumlens.core import analyze, hardware, load_iq, spectrogram
from spectrumlens.cli import main


class Tests(unittest.TestCase):
    def test_tone_and_spectrogram(self):
        rate = 100_000
        samples = np.exp(2j * np.pi * 10_000 * np.arange(4096) / rate).astype(np.complex64)
        report = analyze(samples, rate, 433_920_000, 256)
        self.assertAlmostEqual(report["peaks"][0]["frequency_hz"], 433_930_000, delta=500)
        self.assertTrue(spectrogram(samples, rate, 256)["psd_db"])

    def test_formats_bounds_and_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            samples = np.exp(2j * np.pi * np.arange(1024) / 32).astype(np.complex64)
            samples.tofile(p / "tone.iq")
            self.assertEqual(len(load_iq(p / "tone.iq", "cf32le")), 1024)
            self.assertEqual(main(["analyze", str(p / "tone.iq"), "--format", "cf32le", "--sample-rate", "100000", "--center-hz", "433920000", "--output", str(p / "out.json"), "--csv", str(p / "out.csv")]), 0)
            self.assertTrue((p / "out.csv").exists())
            (p / "bad.iq").write_bytes(b"abc")
            with self.assertRaises(ValueError):
                load_iq(p / "bad.iq", "cf32le")
            with self.assertRaises(ValueError):
                load_iq(p / "tone.iq", "unknown")
        with self.assertRaises(ValueError):
            analyze(np.zeros(64, dtype=np.complex64), 0, 433_920_000, 64)
        self.assertFalse(hardware()[0]["available"])


if __name__ == "__main__":
    unittest.main()
