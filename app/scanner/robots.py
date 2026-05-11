from urllib import robotparser
from urllib.parse import urljoin

import httpx


def can_fetch(url: str, user_agent: str = "*") -> bool:
    """Check robots.txt using httpx so redirects are followed correctly."""
    try:
        robots_url = urljoin(url, "/robots.txt")
        resp = httpx.get(robots_url, timeout=8, follow_redirects=True)
        if resp.status_code != 200:
            return True
        rp = robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(resp.text.splitlines())
        # Allow if either the wildcard or the specific agent permits it
        return rp.can_fetch("*", url) or rp.can_fetch(user_agent, url)
    except Exception:
        return True
