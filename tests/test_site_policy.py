import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Only the server can set this one; a meta element is not allowed to.
HEADER_ONLY = {"frame-ancestors"}


def directives(policy):
    out = {}
    for chunk in policy.split(";"):
        chunk = chunk.strip()
        if chunk:
            name, _, value = chunk.partition(" ")
            out[name] = " ".join(value.split())
    return out


def meta_policy():
    text = (ROOT / "index.html").read_text(encoding="utf-8")
    match = re.search(r'content="(default-src[^"]*)"', text)
    assert match, "index.html carries no content security policy"
    return directives(match.group(1))


def header_policy():
    text = (ROOT / "netlify.toml").read_text(encoding="utf-8")
    match = re.search(r'Content-Security-Policy = "([^"]*)"', text)
    assert match, "netlify.toml carries no content security policy"
    return directives(match.group(1))


class ContentSecurityPolicyTests(unittest.TestCase):
    """The header outlived what it was written for. It allowed scripts and
    styles from unpkg.com, from before Leaflet was served from this origin, and
    the pages had already stopped allowing them. Both policies are enforced, so
    nothing was open in practice — but the header granted a permission with no
    remaining purpose, and it would have taken effect the day the meta element
    was removed."""

    def test_the_header_and_the_pages_state_the_same_policy(self):
        meta, header = meta_policy(), header_policy()
        self.assertEqual(
            {name: value for name, value in header.items() if name not in HEADER_ONLY},
            meta,
            "the served header and the page policy have drifted apart",
        )

    def test_no_third_party_origin_is_allowed_to_run_code(self):
        for name, policy in (("meta", meta_policy()), ("header", header_policy())):
            for directive in ("script-src", "style-src", "default-src"):
                value = policy.get(directive, "")
                self.assertNotIn(
                    "http", value,
                    f"{name} {directive} names a remote origin: {value}",
                )


class FallbackRouteTests(unittest.TestCase):
    """record.html renders its record with script. Until that ran it was the one
    page of 1881 with no heading, so a reader arriving with a screen reader met
    a document that did not say what it was."""

    def test_the_fallback_route_has_a_heading_before_its_script_runs(self):
        text = (ROOT / "record.html").read_text(encoding="utf-8")
        self.assertRegex(text, r"<h1[ >]")

    def test_every_page_has_exactly_one_heading_of_the_first_level(self):
        for page in sorted(ROOT.glob("*.html")):
            count = len(re.findall(r"<h1[ >]", page.read_text(encoding="utf-8")))
            self.assertEqual(count, 1, f"{page.name} carries {count} first-level headings")


if __name__ == "__main__":
    unittest.main()
