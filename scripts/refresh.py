"""Read YangMao's public catalogs and rebuild only the two published snapshots."""

from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://ymtuan.live"
OUTPUT = ROOT / "skills/yangmao-public/references"
MAX_BYTES = 2_000_000
LANGS = {
    "zh": ("", "按主题查找已发布资料", "已发布指南正文", "来源", "核验"),
    "en": ("/en", "Published references by topic", "Published guide text", "Source", "Verified"),
}
LINK = r"\[((?:\\.|[^\]\\\r\n])*)\]\(([^()\s]+)\)"
IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SENSITIVE_QUERY = {
    "access_token", "api_key", "apikey", "authorization", "credential", "password",
    "secret", "session", "sessionid", "sig", "signature", "token",
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def fetch(path, content_type):
    opener = build_opener(NoRedirect())
    request = Request(SITE + path, headers={
        "User-Agent": "YangMao-Skill-Catalog/1.0",
        "Accept-Encoding": "identity",
    })
    try:
        with opener.open(request, timeout=20) as response:
            if (response.status != 200 or response.headers.get_content_type() != content_type
                    or response.headers.get("cf-mitigated") == "challenge"):
                raise ValueError(f"Unexpected response for {path}: HTTP {response.status}")
            payload = response.read(MAX_BYTES + 1)
    except HTTPError as exc:
        raise ValueError(f"{path}: HTTP {exc.code}; stopped") from None
    except (URLError, TimeoutError) as exc:
        raise ValueError(f"{path}: source unavailable ({exc.reason if isinstance(exc, URLError) else 'timeout'})") from None
    if len(payload) > MAX_BYTES:
        raise ValueError(f"{path}: response exceeds the snapshot parser byte limit")
    return payload.decode("utf-8-sig")


def markdown(value):
    text = " ".join(value.split())
    return re.sub(r"([\\\[\]<>])", r"\\\1", text)


def checked_url(value):
    if re.search(r"[\s<>'\x00-\x1f]", value):
        raise ValueError("Invalid public source URL")
    url = urlsplit(value)
    if (url.scheme not in ("http", "https") or not url.hostname or url.username or url.password
            or url.hostname.lower() == "localhost" or url.hostname.endswith((".local", ".test", ".invalid"))
            or any(k.lower() in SENSITIVE_QUERY for k, _ in parse_qsl(url.query, keep_blank_values=True))
            or (url.hostname == "ymtuan.live" and re.match(r"^/(?:en/)?(?:admin|api|orders)(?:/|$)", url.path))):
        raise ValueError("Invalid public source URL")
    return value.replace("(", "%28").replace(")", "%29")


def checked_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Expected an explicit verification date")
    return date.fromisoformat(value).isoformat()


def parse_references(doc, lang):
    prefix, begin, end, source_word, check_word = LANGS[lang]
    head, separator, body = doc.partition(f"\n## {begin}\n")
    body, separator2, _ = body.partition(f"\n## {end}\n")
    if not separator or not separator2:
        raise ValueError(f"{lang}: published reference section not found")
    row = re.compile(rf"^- {LINK} · {source_word}: {LINK} · {check_word}: (\d{{4}}-\d{{2}}-\d{{2}})(?:[T ][^\s]+)?$")
    groups, seen = {}, set()
    for line in body.splitlines():
        if line.startswith("### "):
            title = line[4:].strip()
            groups.setdefault(title, [])
        elif line.startswith("- "):
            match = row.fullmatch(line)
            if not match or not groups:
                raise ValueError(f"{lang}: reference row format changed")
            name, href, label, source, day = match.groups()
            target = urlsplit(href)
            slug = target.path.removeprefix(prefix + "/blog/")
            if (not href.startswith(SITE + prefix + "/blog/") or not IDENTIFIER.fullmatch(slug)
                    or target.query or target.fragment or href in seen):
                raise ValueError(f"{lang}: noncanonical or duplicate article")
            seen.add(href)
            groups[title].append((name, href, label, checked_url(source), checked_date(day)))
    if not seen or any(not entries for entries in groups.values()):
        raise ValueError(f"{lang}: empty or incomplete public reference section")
    advertised = bool(re.search(rf"^- {LINK}$", head, re.M)) and any(
        match.group(2) == SITE + prefix + "/free-ai"
        for match in re.finditer(rf"^- {LINK}$", head, re.M)
    )
    return groups, advertised


class Directory(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical, self.language = "", ""
        self.card, self.capture = None, None
        self.body = []
        self.cards = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.language = attrs.get("lang", "")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href", "")
        classes = attrs.get("class", "").split()
        if tag == "article" and "ym-free" in classes:
            slug = attrs.get("id", "")
            if self.card is not None or not IDENTIFIER.fullmatch(slug):
                raise ValueError("Invalid offer identifier")
            self.card = {"slug": slug, "facts": []}
        if self.card is None:
            return
        for field, style in (("title", "ym-free__name"), ("terms", "ym-free__terms"), ("checked", "ym-free__checked")):
            if style in classes:
                self.capture = (tag, field, [])
        if tag == "dd":
            self.capture = (tag, "fact", [])
        if tag == "a" and "ym-free__go" not in classes:
            self.card["source"] = checked_url(attrs.get("href", ""))

    def handle_data(self, text):
        if self.capture:
            self.capture[2].append(text)
        self.body.append(text)

    def handle_endtag(self, tag):
        if self.capture and self.capture[0] == tag:
            _, field, parts = self.capture
            value = " ".join("".join(parts).split())
            if field == "fact":
                self.card["facts"].append(value)
            else:
                self.card[field] = value
            self.capture = None
        if tag == "article" and self.card is not None:
            self.cards.append(self.card)
            self.card = None


def parse_directory(doc, lang):
    prefix = LANGS[lang][0]
    parser = Directory()
    parser.feed(doc)
    parser.close()
    if parser.canonical != SITE + prefix + "/free-ai" or not parser.language.lower().startswith(lang):
        raise ValueError(f"{lang}: wrong offer directory")
    empty = ("这个分类暂时没有核验有效的条目。" if lang == "zh"
             else "No currently verified offers in this category.")
    if not parser.cards and empty not in " ".join(parser.body):
        raise ValueError(f"{lang}: no offers or known empty state")
    offers, seen = [], set()
    label = "核验 " if lang == "zh" else "Checked "
    for card in parser.cards:
        if (card["slug"] in seen or len(card["facts"]) != 2 or
                not all(card.get(k) for k in ("title", "terms", "source", "checked")) or
                not card["checked"].startswith(label)):
            raise ValueError(f"{lang}: incomplete or duplicate offer {card['slug']}")
        seen.add(card["slug"])
        offers.append((card["slug"], card["title"], card["terms"], " · ".join(card["facts"]),
                       card["source"], checked_date(card["checked"][len(label):])))
    return offers


def render_catalog(groups, offers, lang):
    prefix, _, _, source_word, check_word = LANGS[lang]
    days = [row[-1] for entries in groups.values() for row in entries] + [row[-1] for row in offers or []]
    zh = lang == "zh"
    heading = "# 羊毛团公开资料快照" if zh else "# YangMao public catalog snapshot"
    notice = ("这是网站公开资料的快照。没有明确额度或当前条件时，记为未核实。"
              if zh else "This is a snapshot of the public site. Treat unspecified quotas or current terms as unverified.")
    latest = "最新核验日期（单项见下文）" if zh else "Latest verification date (see individual entries)"
    lines = [heading, "", f"> {notice}", f"> {latest}: {max(days)}",
             f"> [原始公开索引]({SITE}{prefix}/llms.txt)" if zh else f"> [Public source index]({SITE}{prefix}/llms.txt)", ""]
    if offers is not None:
        lines.extend(["## 免费 AI 目录" if zh else "## Free AI directory", ""])
        directory_label = "查看网站上的此栏目" if zh else "Open the directory on the website"
        lines.extend([f"- [{directory_label}]({SITE}{prefix}/free-ai)", ""])
        if not offers:
            lines.extend(["目前没有已核验条目。" if zh else "No verified offers are currently listed.", ""])
        for slug, name, terms, region, source, day in offers:
            rules = "官方规则" if zh else "Official terms"
            lines.extend([f"- [{markdown(name)}]({SITE}{prefix}/free-ai#{slug}) — {markdown(terms)}",
                          f"  {markdown(region)} · [{rules}]({source}) · {check_word}: {day}", ""])
    lines.extend(["## 公开文章链接" if zh else "## Published article links", ""])
    for group, references in groups.items():
        lines.extend([f"### {group}", ""])
        for title, href, label, source, day in references:
            lines.append(f"- [{title}]({href}) · {source_word}: [{label}]({source}) · {check_word}: {day}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def refresh():
    catalogs = {}
    for lang, (prefix, *_) in LANGS.items():
        groups, advertised = parse_references(fetch(prefix + "/llms-full.txt", "text/plain"), lang)
        offers = parse_directory(fetch(prefix + "/free-ai", "text/html"), lang) if advertised else None
        catalogs[OUTPUT / f"catalog-{lang}.md"] = render_catalog(groups, offers, lang)
        print(f"{lang}: {sum(map(len, groups.values()))} article links; {len(offers or [])} public free AI entries")
    for path, text in catalogs.items():
        content = text.encode("utf-8")
        if path.exists() and path.read_bytes() == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", delete=False) as handle:
            handle.write(content)
        Path(handle.name).replace(path)
        print(f"Updated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        refresh()
    except (ValueError, OSError) as exc:
        sys.exit(f"Catalog refresh failed: {exc}")
