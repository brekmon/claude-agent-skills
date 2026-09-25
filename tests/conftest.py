# -*- coding: utf-8 -*-
"""Shared setup.

Skill scripts live under the skill directory, not at the repository root, so
that path goes on sys.path. Nothing here shells out to ffmpeg: `load` decodes
media and is excluded, while everything downstream of it is pure numpy and is
tested directly.
"""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "wildlife-audio-post")
SCRIPTS = os.path.join(SKILL, "scripts")
for p in (ROOT, SCRIPTS):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture
def rng():
    return np.random.default_rng(20260925)


@pytest.fixture
def hiss(rng):
    """Two seconds of constant broadband noise: road, preamp, aircraft. The
    thing that runs 100% of the time."""
    return rng.normal(0.0, 0.05, 96000)


@pytest.fixture
def bird_over_hiss(hiss):
    """The real shape of the problem. A brief, bright transient sitting on a
    constant floor - sound for about 2% of the run, which is exactly why an
    average across the clip measures the noise and not the bird."""
    x = hiss.copy()
    t = np.arange(2000) / 48000.0
    chirp = 0.6 * np.sin(2 * np.pi * 4000 * t) * np.hanning(2000)
    for start in (20000, 50000, 76000):
        x[start:start + 2000] += chirp
    return x
