---
name: wildlife-audio-post
description: Cleaning up location audio for wildlife, nature and outdoor video - removing road hum, aircraft drone, wind and hiss while keeping birdsong, pecks and calls intact. Use this whenever someone says their footage "sounds noisy", "has background hum", "road noise", "an aeroplane went over", or asks about denoising, noise reduction, afftdn, Audition's Noise Reduction, capturing a noise print, matching room tone between shots, or getting audio to -14 LUFS for YouTube. Trigger it even when the request looks like a simple "can you clean this up" or a general Premiere/Audition question, because the measurement discipline here is what separates a fix from an hour of guessing. Also use it before shipping any nature video, to gate the audio.
---

# Wildlife and nature audio, refined

Outdoor location audio is a signal-to-noise problem with an unusual shape: the
subject is **brief and sparse** (a peck, a call, a wingbeat) and the noise is
**constant** (road, aircraft, wind, preamp hiss). Almost every mistake in this
domain comes from measuring the wrong thing and then optimising it.

## The one rule that saves the most time

**Never judge wildlife audio by average energy in a frequency band.**

It is the obvious metric and it is actively misleading. The subject makes sound
maybe 2% of the time; the noise runs 100% of the time. So a "bird band average"
is a **noise measurement wearing a bird costume**. Clean up the noise and the
average falls, and the metric reports that you destroyed the bird.

This exact error cost a full working session: a spectral subtraction pass was
measured as removing "27 dB of bird", was repeatedly weakened and re-run, and
was in fact leaving the pecks completely untouched while dropping the floor.

**Measure separation instead:**

```
separation = P99(short-time level) - P40(short-time level),  measured above 1.5 kHz
```

P99 is the transients — the pecks and calls. P40 is the hum between them. The
difference is what a listener actually judges. Use `scripts/audio_gate.py`.

| separation | verdict |
|---|---|
| ≥ 18 dB | good |
| 14–18 dB | acceptable |
| < 14 dB | it will sound noisy whatever you do — fix it at the mic |

## Workflow

### 1. Pick the mic by measurement, per clip

Multi-channel cameras often record the same mic twice plus a safety track. On a
Sony A7C II the four PCM streams are typically two mics: two bit-identical
channels, and a safety track ~20 dB down.

Check which is actually better **per clip**, not once for the shoot — the answer
changes with wind direction and where the subject is. Compare by **separation**,
not by level and not by band share. A mic that is 10 dB quieter can easily be
the better one, and a mic that scores well on "bird band share" may simply be
bad everywhere.

### 2. High-pass, but know what it does and does not do

A high-pass removes a great deal of **energy** — outdoor recordings often carry
over half their total energy below 200 Hz — and it costs nothing, so always do
it. Around 200–300 Hz is safe for birds; woodpecker pecks keep their body above
200 Hz.

**But energy is not audibility.** The road hum and aircraft drone people
actually complain about sit in the **300–2000 Hz midband**, which a high-pass
barely touches. "I removed 90% of the noise energy" and "it still sounds noisy"
are both true at the same time. Do not stop here and declare victory.

### 3. Denoise with a MEASURED profile, not a generic one

This is the step that does the real work.

**Do not reach for `afftdn` first.** With its own internal estimate it tends to
act as a broadband attenuator: measured on real bird footage it removed 6 dB of
hum while taking **11 dB out of the subject**. It does not discriminate.

**Measured-profile spectral subtraction** does discriminate, because the profile
comes from the clip's own quiet frames:

1. STFT the clip
2. Take the quietest ~10% of frames by total magnitude — that is the noise
3. Median across those frames → the noise profile per bin
4. Subtract `oversubtraction × profile` from every frame's magnitude, with a
   **spectral floor** (keep at least `floor × original`) so nothing goes to
   absolute zero and starts warbling
5. Resynthesise with the original phase

On real footage this dropped the floor 8–14 dB while the transients moved by
**0–1 dB**. See `scripts/denoise.py` for a working implementation.

Starting values: `oversubtraction 2.5–4.0`, `floor 0.06–0.10`. Deeper is often
fine — verify rather than assume, using the warble check below.

**Check for musical noise before committing.** Musical noise is isolated bins
surviving in otherwise-empty frames and warbling frame to frame. Measure it: in
the quietest 25% of frames, take the mean absolute frame-to-frame change in each
bin's level. Compare treated against untreated. Under about 1.3× is inaudible;
much above that and you will hear swirling.

### 4. Match the noise floor across shots

A viewer notices **change** more than level. A cut from a shot with a −18 dB
floor to one with a −4 dB floor reads as the hum lurching, and that is often
what someone means by "the audio is bad" even when each shot alone is fine.

Two fixes, used together:

- **Treat the noisy shots harder** so the floors converge. Clamp the extra
  reduction (about 9 dB) so nothing is processed into sounding hollow.
- **Lengthen the audio cross-fade at the big steps.** Scale it to the step: a
  1–2 dB step is fine at 0.35s; a 14 dB step wants 1.2s so the floor glides.

Aim for a spread of **≤ 6 dB** across the video. `audio_gate.py` reports it.

Note the trap in the other direction: aggressive denoising can push some shots
to near-silence while others keep a floor, and **silence next to hum is also a
noticeable step**. Match the floors, do not just minimise them.

### 5. Loudness — measure on the ENCODED file

Target **−14 LUFS, true peak ≤ −1 dBTP** for YouTube.

**Measure the encoded deliverable, never the intermediate WAV.** Lossy encoding
raises true peak. A master that measured −1.8 dBTP as PCM has shipped at
**+5.9 dBTP as AAC** with samples pinned at the rail.

**The specific trap: a denoiser followed by a hard limiter.** Denoise + limit
made an AAC encoder overshoot by up to **7.7 dB**. Either leave the limiter real
headroom (limit around 0.85 rather than 0.95) or keep them apart — and either
way, encode and measure before believing anything.

**Bound the gain search.** An unbounded solver chasing a loudness target on
quiet nature audio will happily reach +26 dB and saturate. Sweep a bounded range
and keep the **closest passing** value — a fallback that grabs the first or
lowest candidate ships something audibly quiet. If nothing in the range reaches
target, widen the range rather than accepting the edge; denoised nature audio is
quiet and often needs +6 to +9 dB.

## Gate before shipping

```bash
python scripts/audio_gate.py <file-or-folder-of-shots>
```

Reports per-shot floor, peaks and separation, plus the floor spread across the
set. Run it **on the shot segments** while cutting, so a bad shot is caught
before it is baked in, and again on the final encode.

## When post cannot fix it

If separation is under ~14 dB before treatment, no processing will rescue it —
subtracting noise that overlaps the subject removes the subject. Say so plainly
and put the effort at the source: closer mic placement, a shotgun or parabolic
rather than an on-camera capsule, recording with the road downwind, and
capturing **30 seconds of clean room tone** at every setup, which makes every
later decision easier.

## Adobe users

See `references/adobe.md` for the Premiere and Audition equivalents of
everything above — capturing a noise print, the Noise Reduction process, what
maps onto what, and where Adobe's defaults will mislead you in the same way.
