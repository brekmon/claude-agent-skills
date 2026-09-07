# Adobe equivalents — Premiere Pro and Audition

Everything in SKILL.md maps onto Adobe tools. The measurement discipline matters
more than the tool: Adobe's meters will mislead you in exactly the same way an
ffmpeg band average will, because they are also showing you time-averaged level
on a signal whose subject is sparse.

## Getting audio from Premiere to Audition

Right-click the clip → **Edit Clip in Adobe Audition**. Audition works on a copy
and, when you save, Premiere updates the clip in place. Use it for anything
beyond a high-pass; Premiere's Essential Sound panel is too blunt for wildlife
material because its "Reduce Noise" slider behaves like `afftdn` — a broadband
attenuator that takes the subject with the noise.

## The Audition equivalent of a measured noise profile

This is the single most important mapping. Audition's **Capture Noise Print** is
exactly the "measured profile" idea, done by hand instead of statistically:

1. Find a passage with **no subject** — a few seconds of just the road and the
   trees. Longer is better; two seconds is a workable minimum.
2. Select it, then **Effects → Noise Reduction/Restoration → Capture Noise
   Print** (Shift+P).
3. Select the whole clip, open **Noise Reduction (process)** (Ctrl+Shift+P).
4. Set **Noise Reduction** around 40–60% and **Reduce By** around 10–20 dB to
   start. These correspond to the spectral floor and the oversubtraction amount
   in the scripted version.

**Do not push "Reduce By" until the noise vanishes.** The point where the hum
disappears is usually well past the point where the audio starts to warble. Set
it by listening to the *quiet passages between calls* — that is where musical
noise lives — not by listening to the calls.

If the clip has no subject-free passage at all, that is a recording problem, not
a post problem. Take the print from a different clip of the same setup rather
than inventing one.

## Frequency work

Use **Parametric Equalizer** for a high-pass around 200–300 Hz plus a broad dip
in the hum band. A wide, gentle bell around 400–600 Hz at −5 to −8 dB removes a
surprising amount of perceived road noise with **no artifacts at all**, because
it is plain EQ — nothing gated, nothing resynthesised. On real footage this
alone bought ~6 dB while slightly *raising* the subject band.

Reach for EQ before denoising. It costs nothing and it is reversible.

For a tonal drone — a specific aircraft or machinery pitch — the **Spectral
Frequency Display** will show it as a horizontal line. A narrow notch on that
frequency is surgical and free. Look for it rather than assuming the noise is
broadband: a tone reads as low "spectral flatness" and responds to a notch,
where broadband hiss does not.

## What Adobe does not give you

- **A separation number.** Audition shows level, loudness and spectrum, none of
  which is P99-minus-P40. Run `scripts/audio_gate.py` on the exported shots.
- **Floor matching across shots.** You have to compare shots yourself. Audition's
  **Match Loudness** panel matches *loudness*, not noise floor, and on wildlife
  material those are different things — loudness is dominated by the floor, so
  matching loudness can actively make the floors diverge.
- **Encoded-file verification.** Audition measures what is in the session. Export
  the real deliverable and measure that, because AAC raises true peak.

## Room tone

Standard film practice, and it applies here: record 30 seconds of clean ambience
at every setup, on every mic that was running. It gives you a noise print, a bed
to smooth floor changes across cuts, and material to cover edits.

A caution specific to nature channels that promise unmanipulated audio: laying
room tone from one moment under pictures from another is normal post practice,
but it is no longer "the sound recorded at that moment". If the channel makes an
authenticity claim, decide the policy deliberately rather than by habit, and
never use a generated ambience match (iZotope RX and similar) — that is
synthesised audio and it breaks the claim outright.

## Loudness for delivery

Audition's **Match Loudness** panel does ITU-R BS.1770 and can target −14 LUFS
with a true peak ceiling. Set the ceiling to **−1.5 dBTP rather than −1.0** to
leave the encoder room, then export and measure the exported file. If the export
comes back above −1, the limiter and the encoder are fighting; back the limiter
off rather than lowering the target.
