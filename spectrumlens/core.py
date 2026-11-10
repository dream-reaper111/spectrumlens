from pathlib import Path
import importlib.util

import numpy as np
from scipy import signal

MAX_BYTES = 32_000_000
FORMATS = {"cf32le": ("<f4", 8), "cs16le": ("<i2", 4)}


def load_iq(path: Path, sample_format: str) -> np.ndarray:
    if sample_format not in FORMATS:
        raise ValueError("unsupported IQ format")
    size = path.stat().st_size
    dtype, stride = FORMATS[sample_format]
    if not 0 < size <= MAX_BYTES or size % stride:
        raise ValueError("empty, oversized, or truncated IQ file")
    values = np.fromfile(path, dtype=dtype)
    samples = values[0::2].astype(np.float32) + 1j * values[1::2].astype(np.float32)
    if sample_format == "cs16le":
        samples /= 32768
    if not np.all(np.isfinite(samples)):
        raise ValueError("non-finite IQ sample")
    return samples


def analyze(samples: np.ndarray, sample_rate: float, center_hz: float, fft_size: int = 1024) -> dict:
    if not 1_000 <= sample_rate <= 20_000_000 or not 100_000 <= center_hz <= 6_000_000_000:
        raise ValueError("unsupported sample rate or center frequency")
    if fft_size < 64 or fft_size > 8192 or fft_size & (fft_size - 1):
        raise ValueError("FFT size must be power of two from 64 to 8192")
    if len(samples) < fft_size or len(samples) > MAX_BYTES // 4 or not np.all(np.isfinite(samples)):
        raise ValueError("invalid sample count or values")
    freqs, psd = signal.welch(samples, fs=sample_rate, window="hann", nperseg=fft_size, return_onesided=False, scaling="density")
    order = np.argsort(freqs)
    freqs = freqs[order] + center_hz
    power = 10 * np.log10(np.maximum(psd[order], 1e-30))
    floor = float(np.median(power))
    peaks, _ = signal.find_peaks(power, prominence=6)
    ranked = sorted(peaks, key=lambda i: power[i], reverse=True)[:20]
    return {"center_hz": center_hz, "sample_rate": sample_rate, "fft_size": fft_size,
            "sample_count": int(len(samples)), "frequency_hz": freqs.tolist(),
            "psd_db_per_hz": power.tolist(), "noise_floor_estimate_db_per_hz": floor,
            "peaks": [{"frequency_hz": float(freqs[i]), "psd_db_per_hz": float(power[i])} for i in ranked],
            "power_unit_note": "relative digital sample PSD; not calibrated dBm"}


def spectrogram(samples: np.ndarray, sample_rate: float, fft_size: int = 1024) -> dict:
    if len(samples) < fft_size:
        raise ValueError("insufficient samples")
    f, t, s = signal.spectrogram(samples, fs=sample_rate, nperseg=fft_size, noverlap=fft_size // 2,
                                  return_onesided=False, mode="psd")
    indices = np.argsort(f)
    # Bound exported matrix to at most 512 time columns and 1024 frequency bins.
    fi = np.linspace(0, len(f) - 1, min(1024, len(f)), dtype=int)
    ti = np.linspace(0, len(t) - 1, min(512, len(t)), dtype=int)
    return {"offset_hz": f[indices][fi].tolist(), "time_seconds": t[ti].tolist(),
            "psd_db": (10 * np.log10(np.maximum(s[indices][:, ti][fi], 1e-30))).tolist()}


def hardware() -> list[dict]:
    return [{"kind": "receive_only_sdr", "device": "SoapySDR", "available": False,
             "detail": "driver import availability only; device enumeration and RX not verified", "frequency_range_hz": None,
             "sample_rate_limits": None, "operations": ["discovery candidate"] if importlib.util.find_spec("SoapySDR") else [],
             "required_permissions": ["USB or network receiver access"], "driver_dependencies": ["SoapySDR", "device driver"]},
            {"kind": "offline_capture_import", "device": "cf32le/cs16le", "available": True,
             "frequency_range_hz": None, "sample_rate_limits": [1000, 20000000], "operations": ["analyze"],
             "required_permissions": ["file read"], "driver_dependencies": ["NumPy", "SciPy"]},
            {"kind": "local_ble_adapter", "device": None, "available": False, "frequency_range_hz": None, "sample_rate_limits": None, "operations": [], "required_permissions": [], "driver_dependencies": []},
            {"kind": "dedicated_ble_sniffer", "device": None, "available": False, "frequency_range_hz": None, "sample_rate_limits": None, "operations": [], "required_permissions": [], "driver_dependencies": []}]
