# claude-agent-skills

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

## Licence

MIT. See `LICENSE`.
