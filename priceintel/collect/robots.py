"""robots.txt rules with wildcard support.

Python's ``urllib.robotparser`` only does prefix matching, so a rule such as
``Disallow: /*?*`` (used by pro-buket.uz) would be silently ignored. This module follows
the common (Google / RFC 9309) interpretation:

* the group for our user-agent token is used, otherwise the ``*`` group;
* ``*`` matches any characters, a trailing ``$`` anchors the end of the URL path;
* the longest matching rule wins; on a tie, ``Allow`` wins;
* an empty ``Disallow:`` allows everything.
"""
import re
from dataclasses import dataclass, field


@dataclass
class RobotsRules:
    rules: list[tuple[bool, str]] = field(default_factory=list)  # (allow?, pattern)
    crawl_delay: float | None = None
    allow_all: bool = False
    disallow_all: bool = False

    @classmethod
    def allow_everything(cls) -> "RobotsRules":
        """Used when robots.txt does not exist (HTTP 404/410)."""
        return cls(allow_all=True)

    @classmethod
    def deny_everything(cls) -> "RobotsRules":
        """Used when robots.txt cannot be read (5xx, network error): be conservative."""
        return cls(disallow_all=True)

    def allowed(self, path: str) -> bool:
        """``path`` is the URL path plus query string, e.g. ``/shop/page/2/?orderby=price``."""
        if self.disallow_all:
            return False
        if self.allow_all:
            return True
        best_len, best_allow = -1, True
        for allow, pattern in self.rules:
            if _matches(pattern, path):
                n = len(pattern)
                if n > best_len or (n == best_len and allow):
                    best_len, best_allow = n, allow
        return best_allow


def _matches(pattern: str, path: str) -> bool:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    regex = "".join(".*" if ch == "*" else re.escape(ch) for ch in body)
    return re.match(regex + ("$" if anchored else ""), path) is not None


def parse_robots(text: str, agent_token: str) -> RobotsRules:
    """Parse robots.txt and return the rules that apply to ``agent_token``."""
    groups: list[tuple[list[str], list[tuple[bool, str]], float | None]] = []
    agents: list[str] = []
    rules: list[tuple[bool, str]] = []
    delay: float | None = None
    last_was_agent = False

    def close_group():
        if agents:
            groups.append((agents[:], rules[:], delay))

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (s.strip() for s in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if not last_was_agent:  # a new group starts
                close_group()
                agents, rules, delay = [], [], None
            agents.append(value.lower())
            last_was_agent = True
            continue
        last_was_agent = False
        if key in ("allow", "disallow"):
            if value:  # empty Disallow means "allow all" and adds no rule
                rules.append((key == "allow", value))
        elif key == "crawl-delay":
            try:
                delay = float(value)
            except ValueError:
                pass
    close_group()

    token = agent_token.lower()
    specific = [g for g in groups if any(a != "*" and a in token for a in g[0])]
    chosen = specific or [g for g in groups if "*" in g[0]]
    if not chosen:
        return RobotsRules.allow_everything()
    merged_rules = [r for g in chosen for r in g[1]]
    delays = [g[2] for g in chosen if g[2] is not None]
    return RobotsRules(rules=merged_rules, crawl_delay=max(delays) if delays else None)
