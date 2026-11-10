# Architecture

The standalone file loader validates format and size, converts interleaved IQ to complex samples, and rejects non-finite values. SciPy Welch produces relative PSD, SciPy spectrogram produces bounded waterfall data, and peak detection reports prominent bins. The CLI records file SHA-256 and receiver metadata supplied by the operator. JSON/CSV/PNG exports are local. There is no RF transmitter code or shared runtime dependency.
