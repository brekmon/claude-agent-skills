"""
Measured-profile spectral subtraction for wildlife/nature location audio.

    python denoise.py in.wav out.wav [--over 3.0] [--floor 0.08] [--hp 200]
    python denoise.py in.mp4 out.wav --stream 2

Why not afftdn: with its own internal noise estimate it behaves like a broadband
attenuator. Measured on real bird footage it removed 6 dB of hum and took 11 dB
out of the subject. Taking the profile from the clip's own quiet frames instead
means the subtraction knows the shape of THIS clip's noise, so the transients
survive - measured at 0-1 dB loss while the floor dropped 8-14 dB.

Always check the result with audio_gate.py rather than by average band energy,
which on sparse wildlife audio is a noise measurement and will tell you the
subject was destroyed when it was not.
"""
import argparse
import subprocess
import sys
import wave

import numpy as np

SR = 48000
NFFT = 2048
HOP = 512


def load(path, stream=0, hp=200):
    """Decode any media to mono float64 at 48k, with an optional high-pass."""
    af = f"highpass=f={hp}" if hp else "anull"
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-map", f"0:a:{stream}", "-af", af,
         "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True)
    if not r.stdout:
        sys.exit(f"no audio decoded from {path}\n{r.stderr.decode()[-500:]}")
    return np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)


def stft(x):
    w = np.hanning(NFFT)
    n = 1 + max(0, (len(x) - NFFT)) // HOP
    return np.array([np.fft.rfft(x[i * HOP:i * HOP + NFFT] * w) for i in range(n)])


def istft(S, length):
    w = np.hanning(NFFT)
    out = np.zeros(length)
    norm = np.zeros(length)
    for i in range(S.shape[0]):
        a = i * HOP
        seg = np.fft.irfft(S[i]) * w
        out[a:a + NFFT] += seg[:max(0, min(NFFT, length - a))]
        norm[a:a + NFFT] += (w ** 2)[:max(0, min(NFFT, length - a))]
    return out / np.maximum(norm, 1e-9)


def denoise(x, over=3.0, floor=0.08, quiet_pct=10):
    """Subtract a profile measured from the clip's own quietest frames.

    `floor` keeps at least that fraction of the original magnitude in every bin.
    Without it, bins driven to zero flicker in and out between frames, which is
    what musical noise actually is.
    """
    S = stft(x)
    if S.size == 0:
        return x
    mag, phase = np.abs(S), np.angle(S)
    energy = mag.sum(axis=1)
    quiet = mag[energy <= np.percentile(energy, quiet_pct)]
    if len(quiet) == 0:
        return x
    profile = np.median(quiet, axis=0)
    est = np.maximum(mag - over * profile, floor * mag)
    return istft(est * np.exp(1j * phase), len(x))


def warble(x, quiet_pct=25):
    """Musical-noise proxy: frame-to-frame level jitter in the quiet frames.

    Compare treated against untreated. Under about 1.3x is inaudible.
    """
    M = np.abs(stft(x))
    if M.size == 0:
        return 0.0
    e = M.sum(axis=1)
    q = M[e <= np.percentile(e, quiet_pct)]
    if len(q) < 2:
        return 0.0
    return float(np.mean(np.abs(np.diff(20 * np.log10(q + 1e-9), axis=0))))


def separation(x, win=1024):
    """The metric that matters: transients above the floor, above 1.5 kHz."""
    b = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    b[f < 1500] = 0
    hi = np.fft.irfft(b, len(x))
    e = np.array([np.sqrt(np.mean(hi[i:i + win] ** 2)) + 1e-12
                  for i in range(0, len(hi) - win, win)])
    db = 20 * np.log10(e)
    return float(np.percentile(db, 99) - np.percentile(db, 40))


def save(path, x):
    pk = np.max(np.abs(x))
    if pk > 0.98:                      # only touch the scale if it would clip;
        x = x * (0.98 / pk)            # normalising otherwise destroys the level
    with wave.open(path, "wb") as f:   # relationship between shots
        f.setnchannels(1)
        f.setsampwidth(3)
        f.setframerate(SR)
        y = np.clip(x, -1, 1)
        i32 = (y * 8388607).astype("<i4")
        f.writeframes(i32.view("<u1").reshape(-1, 4)[:, :3].tobytes())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--stream", type=int, default=0)
    p.add_argument("--over", type=float, default=3.0)
    p.add_argument("--floor", type=float, default=0.08)
    p.add_argument("--hp", type=int, default=200)
    a = p.parse_args()

    x = load(a.src, a.stream, a.hp)
    y = denoise(x, a.over, a.floor)

    w0, w1 = warble(x), warble(y)
    ratio = w1 / max(w0, 1e-9)
    print(f"  separation  {separation(x):5.1f} dB -> {separation(y):5.1f} dB")
    print(f"  warble      {w0:5.2f} -> {w1:5.2f}  ({ratio:.2f}x untreated)"
          + ("   MUSICAL NOISE LIKELY - reduce --over or raise --floor"
             if ratio > 1.3 else ""))
    save(a.dst, y)
    print(f"  wrote {a.dst}")


if __name__ == "__main__":
    main()
