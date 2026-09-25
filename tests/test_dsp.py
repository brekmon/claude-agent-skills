# -*- coding: utf-8 -*-
"""The signal processing behind the skill.

The skill's central claim is that average energy in a band is the wrong metric,
because the subject sounds for about 2% of a clip and the noise runs for all of
it, so cleaning the noise makes the average fall and the metric reports that you
destroyed the bird. `separation` is the replacement. These tests assert that the
replacement actually has the property the skill claims for it, on signals shaped
like the real problem.
"""
import numpy as np
import pytest

from denoise import HOP, NFFT, denoise, istft, separation, stft, warble


class TestStft:
    def test_frame_and_bin_counts(self, hiss):
        S = stft(hiss)
        assert S.shape == (1 + (len(hiss) - NFFT) // HOP, NFFT // 2 + 1)

    def test_round_trip_is_essentially_exact(self, hiss):
        """Hann windows overlapping at 75% with the analysis window squared in
        the normaliser should reconstruct to floating point noise. If this drifts
        the denoiser is colouring audio before it removes anything."""
        y = istft(stft(hiss), len(hiss))
        interior = slice(2 * NFFT, len(hiss) - 2 * NFFT)
        assert np.max(np.abs(y[interior] - hiss[interior])) < 1e-9

    def test_round_trip_preserves_length(self, hiss):
        assert len(istft(stft(hiss), len(hiss))) == len(hiss)

    def test_input_shorter_than_one_frame_returns_empty_not_a_crash(self):
        """A clip under 43 ms cannot fill a single FFT frame. denoise() already
        guards with `if S.size == 0`, which is proof the author expected an
        empty result here rather than an exception."""
        S = stft(np.zeros(1000))
        assert S.size == 0
        assert S.shape[1] == NFFT // 2 + 1, "shape must stay usable when empty"

    def test_exactly_one_frame(self):
        S = stft(np.zeros(NFFT))
        assert S.shape == (1, NFFT // 2 + 1)


class TestSeparation:
    """The metric the skill exists to promote."""

    def test_constant_noise_scores_low(self, hiss):
        assert separation(hiss) < 2.0

    def test_transients_over_noise_score_high(self, bird_over_hiss):
        assert separation(bird_over_hiss) > 4.0

    def test_it_ranks_the_two_correctly(self, hiss, bird_over_hiss):
        assert separation(bird_over_hiss) > separation(hiss) + 2.0

    def test_scaling_the_whole_clip_does_not_change_it(self, bird_over_hiss):
        """This is the property that makes it a SEPARATION measure and not a
        level measure. Turning the clip down must not look like cleaning it up."""
        quiet = separation(bird_over_hiss * 0.1)
        assert quiet == pytest.approx(separation(bird_over_hiss), abs=0.25)

    def test_low_frequency_rumble_is_ignored(self, bird_over_hiss):
        """It only looks above 1.5 kHz. Adding road rumble underneath must not
        move the score, or every windy morning reads as a different problem."""
        t = np.arange(len(bird_over_hiss)) / 48000.0
        rumble = bird_over_hiss + 0.4 * np.sin(2 * np.pi * 80 * t)
        assert separation(rumble) == pytest.approx(
            separation(bird_over_hiss), abs=0.5)

    def test_the_average_band_energy_trap_is_real(self, bird_over_hiss):
        """Pins the mistake the skill was written about. Denoising REDUCES mean
        energy above 1.5 kHz, so that metric reports damage, while separation
        correctly reports improvement. Both directions asserted, because the
        lesson is the contrast."""
        treated = denoise(bird_over_hiss, over=3.0, floor=0.08)

        def band_mean(x):
            b = np.fft.rfft(x)
            f = np.fft.rfftfreq(len(x), 1 / 48000.0)
            b[f < 1500] = 0
            return float(np.mean(np.abs(np.fft.irfft(b, len(x)))))

        assert band_mean(treated) < band_mean(bird_over_hiss), \
            "average band energy falls - the misleading reading"
        assert separation(treated) > separation(bird_over_hiss), \
            "separation rises - the reading that matches what you hear"


class TestDenoise:
    def test_length_is_preserved(self, bird_over_hiss):
        assert len(denoise(bird_over_hiss)) == len(bird_over_hiss)

    def test_the_noise_floor_comes_down(self, bird_over_hiss):
        """Measured between the calls, where there is nothing but hiss."""
        treated = denoise(bird_over_hiss, over=3.0, floor=0.08)
        gap = slice(30000, 45000)
        before = np.sqrt(np.mean(bird_over_hiss[gap] ** 2))
        after = np.sqrt(np.mean(treated[gap] ** 2))
        assert after < before * 0.8

    def test_the_transients_survive(self, bird_over_hiss):
        """The whole point. A denoiser that flattens the floor and the bird with
        it has done nothing useful."""
        treated = denoise(bird_over_hiss, over=3.0, floor=0.08)
        call = slice(20000, 22000)
        before = np.max(np.abs(bird_over_hiss[call]))
        after = np.max(np.abs(treated[call]))
        assert after > before * 0.5

    def test_the_spectral_floor_is_respected(self, bird_over_hiss):
        """`floor` keeps at least that fraction of every bin. Bins driven to
        absolute zero flicker between frames, and that flicker IS musical noise."""
        S = np.abs(stft(bird_over_hiss))
        treated = np.abs(stft(denoise(bird_over_hiss, over=50.0, floor=0.20)))
        n = min(S.shape[0], treated.shape[0])
        ratio = treated[:n][S[:n] > 1e-6] / S[:n][S[:n] > 1e-6]
        assert np.percentile(ratio, 1) > 0.05

    def test_heavier_oversubtraction_removes_more(self, bird_over_hiss):
        gap = slice(30000, 45000)
        light = np.sqrt(np.mean(denoise(bird_over_hiss, over=1.5)[gap] ** 2))
        heavy = np.sqrt(np.mean(denoise(bird_over_hiss, over=5.0)[gap] ** 2))
        assert heavy < light

    def test_a_clip_too_short_to_analyse_is_returned_untouched(self):
        x = np.zeros(1000)
        assert np.array_equal(denoise(x), x)


class TestWarble:
    def test_it_returns_a_number_for_normal_audio(self, bird_over_hiss):
        assert warble(bird_over_hiss) > 0

    def test_silence_does_not_divide_by_zero(self):
        assert np.isfinite(warble(np.zeros(96000)))

    def test_too_short_to_analyse_returns_zero(self):
        assert warble(np.zeros(1000)) == 0.0

    def test_warble_is_not_monotonic_in_aggression(self, bird_over_hiss):
        """Measured, not assumed. I expected savage settings to warble more than
        gentle ones. They do not, and the reason is worth knowing before anyone
        trusts this number as a safety dial.

        With a very low spectral floor, oversubtraction drives nearly every bin
        in a quiet frame down to `floor x magnitude`. That is a PROPORTIONAL
        scaling, and warble is measured in dB, where a constant scale factor
        cancels out of a frame-to-frame difference. So the deepest settings can
        score close to untreated audio while sounding their worst.

        Musical noise comes from bins PARTIALLY surviving and flickering, which
        is a middle setting, not an extreme one. The metric is a proxy, exactly
        as its docstring says. Compare treated against untreated and still
        listen."""
        gentle = warble(denoise(bird_over_hiss, over=1.5, floor=0.15))
        savage = warble(denoise(bird_over_hiss, over=8.0, floor=0.01))
        assert gentle > 0 and savage > 0
        assert savage < gentle, (
            "if this ever reverses, the dB scale-invariance argument above no "
            "longer holds and the guidance in SKILL.md should be revisited")

    def test_a_constant_gain_does_not_change_warble(self, bird_over_hiss):
        """The mechanism behind the test above, isolated."""
        assert warble(bird_over_hiss * 0.25) == pytest.approx(
            warble(bird_over_hiss), abs=1e-6)
