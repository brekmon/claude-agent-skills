# -*- coding: utf-8 -*-
"""The skill manifest itself.

A skill is loaded by an agent, not run by a person, and that changes what
failure looks like. If SKILL.md points at a script that does not exist, nothing
raises. The agent reads an instruction, tries to follow it, finds nothing, and
carries on with whatever it can manage. The user sees a slightly worse answer
and never learns a file was missing.

That is the same class of failure the skill itself is about, so it gets the same
treatment: check it, do not assume it.
"""
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = [d for d in sorted(os.listdir(ROOT))
          if os.path.isfile(os.path.join(ROOT, d, "SKILL.md"))]


def read(skill):
    with open(os.path.join(ROOT, skill, "SKILL.md"), encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def test_at_least_one_skill_is_present():
    assert SKILLS, "no SKILL.md found anywhere in the repository"


@pytest.mark.parametrize("skill", SKILLS)
class TestManifest:
    def test_has_frontmatter_with_name_and_description(self, skill):
        fm = frontmatter(read(skill))
        assert fm.get("name"), "%s: SKILL.md has no name in its frontmatter" % skill
        assert fm.get("description"), "%s: no description" % skill

    def test_name_matches_the_directory(self, skill):
        """The directory name is how the skill is invoked. A mismatch means the
        thing you call and the thing that loads are different names."""
        assert frontmatter(read(skill))["name"] == skill

    def test_description_is_substantial_enough_to_match_on(self, skill):
        """Discovery is the whole game. A skill nobody's request matches might
        as well not exist, so the description has to carry trigger phrases."""
        assert len(frontmatter(read(skill))["description"]) > 200

    def test_every_referenced_file_exists(self, skill):
        """The silent failure this file was written for."""
        text = read(skill)
        refs = set(re.findall(r"`((?:scripts|references|assets)/[^`]+)`", text))
        missing = [r for r in sorted(refs)
                   if not os.path.exists(os.path.join(ROOT, skill, r))]
        assert missing == [], "%s references files that do not exist: %s" % (
            skill, missing)

    def test_every_script_is_referenced_somewhere(self, skill):
        """The reverse check. A script nothing points at is either dead weight
        or, worse, the working implementation of something the skill is telling
        the agent to find elsewhere."""
        sdir = os.path.join(ROOT, skill, "scripts")
        if not os.path.isdir(sdir):
            pytest.skip("no scripts directory")
        text = read(skill)
        orphans = [s for s in sorted(os.listdir(sdir))
                   if s.endswith(".py") and s not in text]
        assert orphans == [], "%s: scripts never mentioned in SKILL.md: %s" % (
            skill, orphans)

    def test_scripts_are_importable(self, skill):
        """A skill whose tooling does not even parse is worse than one with no
        tooling, because the agent will try."""
        import py_compile
        sdir = os.path.join(ROOT, skill, "scripts")
        if not os.path.isdir(sdir):
            pytest.skip("no scripts directory")
        for s in sorted(os.listdir(sdir)):
            if s.endswith(".py"):
                py_compile.compile(os.path.join(sdir, s), doraise=True)
