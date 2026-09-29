"""Build HTML and plain Markdown from one source; validate local published links."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".docs-src"
SITE = ROOT / "site"
SITE_URL = "https://mate4b.github.io/narrative-contracts/"
REPO_URL = "https://github.com/Mate4b/narrative-contracts/blob/main/"
LINK = re.compile(r"(!?\[[^\]\n]*\]\()([^\s)]+)(\))")
EXAMPLES = (
    "examples/first_audit.py",
    "examples/audit_existing_validator.py",
    "examples/external_validators.py",
    "examples/five_minute_demo.py",
    "examples/mutation_audit.py",
    "examples/pydantic_reply.py",
    "examples/valid.json",
)


def prepare() -> dict[str, str]:
    # Explicit publication allowlist; never copy the workspace or private app fixtures.
    sources = [ROOT / name for name in ("README.md", "AGENTS.md", "CONTRIBUTING.md")]
    sources += sorted((ROOT / "docs").glob("*.md"))
    sources += sorted((ROOT / "paper").glob("*.md"))
    sources = [p for p in sources if p.name != "launch-draft.md"]
    mapping = {p.relative_to(ROOT).as_posix(): p.relative_to(ROOT).as_posix() for p in sources}
    mapping["README.md"] = "index.md"
    for name in (*EXAMPLES, "llms.txt"):
        mapping[name] = name
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir()
    hashes = {}
    for src, dst in mapping.items():
        path = ROOT / src
        data = path.read_bytes()
        hashes[src] = hashlib.sha256(data).hexdigest()
        target = STAGE / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".md":

            def rewrite(match: re.Match[str]) -> str:
                original = match[2]
                parts = urlsplit(original)
                if parts.scheme or parts.netloc or not parts.path or original.startswith("/"):
                    return match[0]
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(src), parts.path))
                if not (ROOT / resolved).exists():
                    raise ValueError(f"Missing source link in {src}: {original}")
                if resolved in mapping:
                    url = posixpath.relpath(mapping[resolved], posixpath.dirname(dst) or ".")
                else:
                    url = REPO_URL + resolved
                if parts.query:
                    url += "?" + parts.query
                if parts.fragment:
                    url += "#" + parts.fragment
                return match[1] + url + match[3]

            target.write_text(LINK.sub(rewrite, data.decode()), encoding="utf-8")
        else:
            target.write_bytes(data)
    return hashes


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"href", "src"} and value:
                self.urls.append(value)


def validate() -> int:
    checked = 0
    errors = []
    for page in SITE.rglob("*.html"):
        # MkDocs' generic 404 template deliberately has relative navigation.
        if page.name == "404.html":
            continue
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        base = SITE_URL + page.relative_to(SITE).as_posix()
        for link in parser.urls:
            url = urljoin(base, link)
            if not url.startswith(SITE_URL):
                continue
            relative = unquote(urlsplit(url[len(SITE_URL) :]).path)
            target = SITE / relative
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{page.relative_to(SITE)} -> {link}")
            checked += 1
    # Also check every canonical machine-documentation link.
    for match in LINK.finditer((SITE / "llms.txt").read_text()):
        url = match[2]
        if url.startswith(SITE_URL):
            target = SITE / urlsplit(url[len(SITE_URL) :]).path
            if not target.is_file():
                errors.append(f"llms.txt -> {url}")
            checked += 1
    if errors:
        raise ValueError("Broken published links:\n" + "\n".join(errors))
    return checked


def main() -> None:
    hashes = prepare()
    subprocess.run([sys.executable, "-m", "mkdocs", "build", "--strict"], cwd=ROOT, check=True)
    # MkDocs renders Markdown into HTML; expose the same text for agent clients.
    for source in STAGE.rglob("*.md"):
        target = SITE / source.relative_to(STAGE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (SITE / ".nojekyll").touch()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    (SITE / "build-info.json").write_text(
        json.dumps({"revision": revision, "source_sha256": hashes}, indent=2) + "\n"
    )
    checked = validate()
    print(f"Built {len(hashes)} source files; checked {checked} local HTML and llms.txt links.")


if __name__ == "__main__":
    main()
