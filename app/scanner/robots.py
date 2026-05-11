from urllib import robotparser
from urllib.parse import urljoin


def can_fetch(url: str, user_agent: str = "*") -> bool:
    try:
        rp = robotparser.RobotFileParser()
        robots_url = urljoin(url, "/robots.txt")
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        # Si falla robots, permitir pero mantener crawling conservador
        return True
