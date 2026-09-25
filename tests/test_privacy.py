# -*- coding: utf-8 -*-
"""The privacy gate, and what git is allowed to track.

Enforcement that only runs on the author's laptop is not enforcement, so these
run in CI on every push.
"""
import os
import subprocess

import pytest

import privacy_check

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tracked():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=REPO)
    return [f for f in out.stdout.split() if f]


class TestNothingPrivateIsTracked:
    def test_the_word_list_is_not_committed(self):
        """The list of terms the gate screens for is itself the leak."""
        assert ".private-terms" not in tracked()

    @pytest.mark.parametrize("suffix", [".wav", ".mp4", ".MP4", ".mov", ".json", ".log"])
    def test_no_media_or_run_output_is_committed(self, suffix):
        bad = [f for f in tracked() if f.endswith(suffix)]
        assert bad == [], "%s files are tracked: %s" % (suffix, bad)

    def test_no_absolute_user_paths_appear_in_tracked_files(self):
        """A hard-coded home-directory path names the machine's user. The
        markers are ASSEMBLED rather than spelled out, because in the sibling
        repo the first version of this test failed on itself: the file contained
        the literal strings it was scanning for. Excluding the test from its own
        scan would leave a hole exactly where someone is most likely to paste a
        real path."""
        sep = chr(92)
        u, h = "Users", "home"
        markers = ["C:" + sep + u + sep, "C:/" + u + "/", "/" + h + "/",
                   sep + u + sep]
        hits = []
        for f in tracked():
            path = os.path.join(REPO, f)
            if not os.path.isfile(path):
                continue
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if any(m in text for m in markers):
                hits.append(f)
        assert hits == [], "absolute user paths found in: %s" % hits


class TestLoadTerms:
    def test_missing_file_stops_rather_than_passing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(privacy_check, "TERMS_FILE", str(tmp_path / "nope"))
        with pytest.raises(SystemExit):
            privacy_check.load_terms()

    def test_empty_file_stops_rather_than_passing(self, tmp_path, monkeypatch):
        """An empty gate always passes, which is the same as having no gate."""
        f = tmp_path / "terms"
        f.write_text("# just a comment\n\n", encoding="utf-8")
        monkeypatch.setattr(privacy_check, "TERMS_FILE", str(f))
        with pytest.raises(SystemExit):
            privacy_check.load_terms()

    def test_terms_are_loaded_counted_and_case_insensitive(self, tmp_path, monkeypatch):
        f = tmp_path / "terms"
        f.write_text("# comment\nSomeplace Road\nC0527\n\n", encoding="utf-8")
        monkeypatch.setattr(privacy_check, "TERMS_FILE", str(f))
        pattern, n = privacy_check.load_terms()
        assert n == 2
        assert pattern.search("shot on someplace road")
        assert pattern.search("clip c0527")
        assert not pattern.search("nothing to see")

    def test_regex_characters_in_a_term_are_escaped(self, tmp_path, monkeypatch):
        f = tmp_path / "terms"
        f.write_text("A. Person\n", encoding="utf-8")
        monkeypatch.setattr(privacy_check, "TERMS_FILE", str(f))
        pattern, _n = privacy_check.load_terms()
        assert pattern.search("A. Person")
        assert not pattern.search("AXPerson"), "the dot must be literal, not a wildcard"
