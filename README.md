# claude-agent-skills

[![CI](https://github.com/brekmon/claude-agent-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/brekmon/claude-agent-skills/actions/workflows/ci.yml)

A production Claude Code agent skill, written to encode specialist domain
knowledge into a repeatable workflow rather than re-explaining it every session.

---

## Why a skill instead of a long prompt

A prompt is advice. A skill is a contract: it decides when it should fire, what
the agent must do, and what it is not allowed to conclude. It carries executable
tooling, so measurements are taken rather than estimated.

## Architecture: progressive disclosure

```
wildlife-audio-post/
  SKILL.md          <- routing layer, always loaded: when to fire, the workflow,
                       and the rules that must not be broken
  references/       <- loaded on demand, only when that topic comes up
  scripts/          <- executable tooling the agent runs directly
```

The router stays small so it is always cheap to load. Reference material is
pulled in only when the task reaches that topic. Scripts run instead of the
model estimating, because a model guessing at a loudness figure is worse than
useless: it is confidently wrong.

## What this skill does

`wildlife-audio-post` cleans location audio for wildlife and outdoor video:
removing road hum, aircraft drone, wind and hiss while keeping birdsong, pecks
and calls intact.

The part that matters is not the filter chain, it is the **measurement
discipline**. The skill refuses to judge a denoise by ear or by average band
energy, because averaging across a clip is dominated by constant hum while the
subject only makes sound occasionally. That mistake once reported a successful
denoise as destroying the bird. The corrected metric, and the postmortem, are
both in the skill.

Bundled tooling:

- `scripts/audio_gate.py` — measures subject-to-noise separation as one number
- `scripts/denoise.py` — measured-profile spectral subtraction

## Design rules carried into the skill

- **A check only counts if a tool produced the number, or a human listened.**
- Capture a noise print from real room tone, never synthesise one.
- Measure before and after, on the same scale, and report both.
- Deliver to a stated spec (-14 LUFS, -1 dBTP) rather than to taste.

## A second skill is deliberately not published

The other skill in daily use covers personal family-archive editing. It names
real people, including children, so it stays private. Deciding what not to
publish is part of building these.

---

## Tests

```
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

41 tests, run on every push against Python 3.10 through 3.13. No ffmpeg needed:
`load` decodes media and is excluded, and everything downstream of it is pure
numpy tested on synthetic signals shaped like the real problem, a brief bright
transient sitting on a constant floor.

Two things are tested that would otherwise fail silently.

**The metric the skill exists to promote.** The central claim is that average
energy in a band is the wrong measurement, because the subject sounds for about
2% of a clip while the noise runs for all of it. One test denoises a synthetic
clip and asserts both readings at once: mean energy above 1.5 kHz falls, which
is the misleading result that started all this, while `separation` rises, which
matches what you hear. The claim is not asserted in prose, it is demonstrated.
`separation` is also shown to be scale-invariant, so turning a clip down cannot
look like cleaning it up, and unaffected by low-frequency rumble.

**The manifest.** A skill is loaded by an agent, not run by a person, and that
changes what failure looks like. If `SKILL.md` points at a script that does not
exist, nothing raises: the agent reads the instruction, finds nothing, and
carries on with whatever it can manage. Tests check every referenced path
exists, and the reverse, that no script sits in the repository unmentioned.
Both directions caught the same real bug on their first run.

One test asserts a property I got wrong on purpose to record it. Aggressive
oversubtraction does **not** warble more than gentle settings, because with a
very low spectral floor almost every bin is scaled proportionally, and a
constant scale factor cancels out of a dB difference. Musical noise comes from
bins partially surviving, which is a middle setting rather than an extreme one.
The metric is a proxy, exactly as its docstring says.

---

## Licence

MIT. See `LICENSE`.
