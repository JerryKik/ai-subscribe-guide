#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面级 SEO 检测：H1、title、meta description、canonical、URL slug。

使用 Python 标准库 html.parser 解析 HTML，无需 BeautifulSoup。
向 stdout 输出结构化 JSON，供 Agent 直接消费。

用法:
    python3 check-page.py https://example.com
    python3 check-page.py https://example.com --timeout 20
    python3 check-page.py https://example.com --keyword "running shoes"

依赖:
    pip install requests
    （HTML 解析仅用标准库 html.parser）

TD 长度阈值默认读取同目录 td_check_defaults.json（与 seo_frontmatter.md 一致：
title 40–60、description 140–160）。
说明文档: CHECK_PAGE_SEO.md
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import socket
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print(
        "Error: requests library required. Install with: "
        "pip install -r requirements-seo-check.txt",
        file=sys.stderr,
    )
    sys.exit(1)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 ClaudeSEO/1.2"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "not", "no",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
    "is", "are", "was", "were", "be",
    "it", "its", "this", "that",
})

_SLUG_STOP_WORDS = frozenset({
    "a", "the", "and", "of", "or", "in", "on", "at", "to", "for", "with", "by", "from",
})

_SLUG_SAFE_RE = re.compile(r"[^a-z0-9\-/]")

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_TD_PATH = _SCRIPT_DIR / "td_check_defaults.json"

# 回退阈值（与 td_check_defaults.json 一致）
_FALLBACK_TITLE_RANGE = (40, 60)
_FALLBACK_DESC_RANGE = (140, 160)


def _load_td_ranges(defaults_path: Optional[Path] = None) -> tuple[tuple[int, int], tuple[int, int]]:
    """加载 title / meta description 字符长度区间。"""
    path = defaults_path or _DEFAULT_TD_PATH
    if not path.is_file():
        return _FALLBACK_TITLE_RANGE, _FALLBACK_DESC_RANGE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        t = data.get("title") or {}
        d = data.get("description") or {}
        title_range = (int(t["min"]), int(t["max"]))
        desc_range = (int(d["min"]), int(d["max"]))
        return title_range, desc_range
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return _FALLBACK_TITLE_RANGE, _FALLBACK_DESC_RANGE


def _fetch(
    url: str,
    timeout: int,
) -> tuple[Optional[int], Optional[str], str, list[dict[str, Any]], Optional[str]]:
    """
    抓取页面（含 SSRF 防护）。

    Returns:
        (status_code, content, final_url, redirect_chain, error)
    """
    parsed = urlparse(url)

    try:
        hostname = parsed.hostname or ""
        resolved_ip = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(resolved_ip)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            return (
                None,
                None,
                url,
                [],
                f"Blocked: resolves to private IP ({resolved_ip})",
            )
    except (socket.gaierror, ValueError):
        pass

    try:
        session = requests.Session()
        session.max_redirects = 5
        resp = session.get(
            url,
            headers=_DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        redirect_chain = [
            {"url": r.url, "status_code": r.status_code} for r in resp.history
        ]
        return resp.status_code, resp.text, resp.url, redirect_chain, None
    except requests.exceptions.Timeout:
        return None, None, url, [], f"Timed out after {timeout}s"
    except requests.exceptions.TooManyRedirects:
        return None, None, url, [], "Too many redirects (max 5)"
    except requests.exceptions.SSLError as exc:
        return None, None, url, [], f"SSL error: {exc}"
    except requests.exceptions.ConnectionError as exc:
        return None, None, url, [], f"Connection error: {exc}"
    except requests.exceptions.RequestException as exc:
        return None, None, url, [], f"Request failed: {exc}"


class _SEOParser(HTMLParser):
    """轻量 SEO 元素提取：title、h1、meta description、canonical。"""

    def __init__(self) -> None:
        super().__init__()
        self.title: Optional[str] = None
        self._in_title = False
        self._title_buf = ""
        self.h1_values: list[str] = []
        self._in_h1 = False
        self._h1_depth = 0
        self._h1_buf = ""
        self.meta_description: Optional[str] = None
        self.canonical: Optional[str] = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, Optional[str]]],
    ) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag == "title" and self.title is None:
            self._in_title = True
            self._title_buf = ""

        elif tag == "h1":
            self._in_h1 = True
            self._h1_depth += 1
            self._h1_buf = ""

        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            if name == "description" and self.meta_description is None:
                self.meta_description = attrs_dict.get("content", "")

        elif tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            if "canonical" in rel and self.canonical is None:
                self.canonical = attrs_dict.get("href", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = self._title_buf.strip() or None

        elif tag == "h1" and self._in_h1:
            self._h1_depth -= 1
            if self._h1_depth <= 0:
                self._in_h1 = False
                self._h1_depth = 0
                text = self._h1_buf.strip()
                if text:
                    self.h1_values.append(text)

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_buf += data
        if self._in_h1:
            self._h1_buf += data


def _keyword_match_fields(
    text_lower: str,
    keyword: str,
) -> tuple[str, bool, str]:
    """
    字符串级关键词匹配。

    Returns:
        (keyword_match, llm_review_required, note)
    """
    kw_lower = keyword.lower().strip()
    kw_words = [w for w in kw_lower.split() if w not in _STOP_WORDS]
    full_match = kw_lower in text_lower
    partial_match = not full_match and any(w in text_lower for w in kw_words)

    if full_match:
        return (
            "full",
            False,
            f'Primary keyword "{keyword}" found (full match).',
        )
    if partial_match:
        return (
            "partial",
            True,
            (
                f'Partial string match for "{keyword}". '
                "LLM review required: does this cover the keyword's search intent?"
            ),
        )
    return (
        "none",
        False,
        f'Primary keyword "{keyword}" not found.',
    )


def _check_h1(h1_values: list[str], keyword: Optional[str] = None) -> dict[str, Any]:
    count = len(h1_values)
    keyword_match = "unverified"
    llm_review_required = False
    keyword_note = ""

    if count == 0:
        return {
            "status": "fail",
            "count": 0,
            "values": [],
            "keyword_match": keyword_match,
            "llm_review_required": llm_review_required,
            "detail": (
                "No H1 tag found. Every page should have exactly one H1 "
                "containing the primary keyword."
            ),
        }

    if count > 1:
        return {
            "status": "fail",
            "count": count,
            "values": h1_values,
            "keyword_match": keyword_match,
            "llm_review_required": llm_review_required,
            "detail": (
                f"{count} H1 tags found. Keep exactly one H1; include the "
                "primary keyword or a natural variant."
            ),
        }

    h1_text = h1_values[0]
    if not h1_text.strip():
        return {
            "status": "fail",
            "count": 1,
            "values": h1_values,
            "keyword_match": keyword_match,
            "llm_review_required": llm_review_required,
            "detail": "H1 tag present but content is empty.",
        }

    length = len(h1_text)
    issues: list[str] = []

    if length < 5:
        issues.append(
            f'H1 is very short ({length} chars): "{h1_text}". '
            "Likely brand-name only — add the primary keyword."
        )
    elif length > 70:
        issues.append(
            f"H1 is {length} characters — consider trimming to under 70."
        )

    if keyword:
        keyword_match, llm_review_required, keyword_note = _keyword_match_fields(
            h1_text.lower(),
            keyword,
        )
        if keyword_match == "partial":
            issues.append(keyword_note)
        elif keyword_match == "none":
            issues.append(
                f'{keyword_note} H1: "{h1_text}". '
                "Include the primary keyword or a natural variant."
            )
    else:
        issues.append(
            "No --keyword provided. Pass --keyword <term> to enable keyword check."
        )

    if issues:
        return {
            "status": "warn",
            "count": 1,
            "values": h1_values,
            "keyword_match": keyword_match,
            "llm_review_required": llm_review_required,
            "detail": " | ".join(issues),
        }

    detail = f'Single H1 found: "{h1_text}".'
    if keyword_note:
        detail += f" {keyword_note}"
    return {
        "status": "pass",
        "count": 1,
        "values": h1_values,
        "keyword_match": keyword_match,
        "llm_review_required": llm_review_required,
        "detail": detail.strip(),
    }


def _check_title(
    title: Optional[str],
    keyword: Optional[str] = None,
    title_range: tuple[int, int] = _FALLBACK_TITLE_RANGE,
) -> dict[str, Any]:
    t_min, t_max = title_range
    keyword_match = "unverified"
    keyword_position = "unverified"
    llm_review_required = False

    if not title:
        return {
            "status": "fail",
            "value": None,
            "length": 0,
            "length_range": list(title_range),
            "keyword_match": keyword_match,
            "keyword_position": keyword_position,
            "llm_review_required": llm_review_required,
            "detail": "No <title> tag found. Title is a critical on-page SEO element.",
        }

    length = len(title)
    issues: list[str] = []
    notes: list[str] = []

    if length < 10:
        issues.append(
            f"Title is only {length} characters — likely a placeholder or too short."
        )
    elif length > t_max:
        issues.append(
            f"Title is {length} characters — may be truncated in SERPs "
            f"(recommended {t_min}-{t_max})."
        )
    elif length < t_min:
        issues.append(
            f"Title is {length} characters — below site minimum "
            f"(recommended {t_min}-{t_max})."
        )
    else:
        notes.append(
            f"Length {length} chars — within site range ({t_min}-{t_max})."
        )

    if keyword:
        title_lower = title.lower()
        kw_lower = keyword.lower().strip()
        keyword_match, kw_llm, kw_note = _keyword_match_fields(title_lower, keyword)

        if keyword_match == "full":
            pos = title_lower.find(kw_lower)
            if pos <= 30:
                keyword_position = "start"
                notes.append(kw_note + " Keyword leads the title — good positioning.")
            else:
                keyword_position = "middle"
                issues.append(
                    f'Keyword "{keyword}" at position {pos} — '
                    "best practice: lead with primary keyword (within first 30 chars)."
                )
                llm_review_required = True
        elif keyword_match == "partial":
            keyword_position = "middle"
            llm_review_required = kw_llm
            issues.append(f'{kw_note} Title: "{title}".')
        else:
            keyword_position = "absent"
            issues.append(
                f'{kw_note} Lead with the primary keyword for strongest SEO signal.'
            )
    else:
        llm_review_required = True
        issues.append(
            "No --keyword provided. LLM review: verify title starts with "
            "the primary keyword and reads naturally."
        )

    detail_parts = issues + notes
    status = "fail" if length < 10 or length > t_max or length < t_min else (
        "warn" if issues else "pass"
    )

    return {
        "status": status,
        "value": title,
        "length": length,
        "length_range": list(title_range),
        "keyword_match": keyword_match,
        "keyword_position": keyword_position,
        "llm_review_required": llm_review_required,
        "detail": " | ".join(detail_parts),
    }


def _check_meta_description(
    meta_desc: Optional[str],
    keyword: Optional[str] = None,
    desc_range: tuple[int, int] = _FALLBACK_DESC_RANGE,
) -> dict[str, Any]:
    d_min, d_max = desc_range
    keyword_match = "unverified"

    if meta_desc is None:
        return {
            "status": "fail",
            "value": None,
            "length": 0,
            "length_range": list(desc_range),
            "keyword_match": keyword_match,
            "llm_review_required": False,
            "detail": (
                "No <meta name='description'> found. "
                "Missing meta descriptions reduce SERP snippet quality."
            ),
        }

    if not meta_desc.strip():
        return {
            "status": "warn",
            "value": "",
            "length": 0,
            "length_range": list(desc_range),
            "keyword_match": keyword_match,
            "llm_review_required": False,
            "detail": "Meta description tag present but content is empty.",
        }

    length = len(meta_desc)
    issues: list[str] = []
    notes: list[str] = []

    if length < d_min - 40:
        issues.append(
            f"Length {length} chars — too short (site range {d_min}-{d_max})."
        )
    elif length > d_max:
        issues.append(
            f"Length {length} chars — may be truncated in SERPs "
            f"(site range {d_min}-{d_max})."
        )
    elif length < d_min:
        issues.append(
            f"Length {length} chars — below site minimum ({d_min}-{d_max})."
        )
    else:
        notes.append(
            f"Length {length} chars — within site range ({d_min}-{d_max})."
        )

    if keyword:
        keyword_match, _, kw_note = _keyword_match_fields(
            meta_desc.lower(),
            keyword,
        )
        if keyword_match == "full":
            notes.append(kw_note)
        elif keyword_match == "partial":
            issues.append(kw_note)
        else:
            issues.append(
                f'{kw_note} Include the primary keyword or a natural synonym once.'
            )
    else:
        notes.append("No --keyword provided. Keyword presence not checked.")

    llm_review_required = True
    notes.append(
        "LLM review: (1) complete sentence? (2) concrete result not vague fluff? "
        "(3) keyword natural, not stuffed? (4) more specific than typical competitor?"
    )

    status = "warn" if issues else "pass"
    return {
        "status": status,
        "value": meta_desc,
        "length": length,
        "length_range": list(desc_range),
        "keyword_match": keyword_match,
        "llm_review_required": llm_review_required,
        "detail": " | ".join(issues + notes),
    }


def _check_canonical(canonical: Optional[str], final_url: str) -> dict[str, Any]:
    if not canonical:
        return {
            "status": "warn",
            "value": None,
            "matches_final_url": False,
            "detail": (
                "No <link rel='canonical'> found. "
                "Without a canonical tag, duplicate content issues may arise."
            ),
        }

    canonical_norm = canonical.rstrip("/")
    final_norm = final_url.rstrip("/")
    matches = canonical_norm == final_norm

    if matches:
        return {
            "status": "pass",
            "value": canonical,
            "matches_final_url": True,
            "detail": "Self-referencing canonical present.",
        }

    return {
        "status": "warn",
        "value": canonical,
        "matches_final_url": False,
        "detail": (
            f"Canonical points to a different URL: {canonical}. "
            f"Final page URL is: {final_url}. "
            "Verify this is intentional and not a misconfiguration."
        ),
    }


def _check_url_slug(url: str, keyword: Optional[str] = None) -> dict[str, Any]:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"

    if path in ("/", ""):
        return {
            "status": "pass",
            "slug": "/",
            "is_homepage": True,
            "keyword_match": "unverified",
            "llm_review_required": False,
            "detail": "Homepage detected — URL slug check not applicable.",
        }

    slug = path
    segments = [s for s in path.split("/") if s]
    issues: list[str] = []
    notes: list[str] = []
    keyword_match = "unverified"
    llm_review_required = False

    if slug != slug.lower():
        issues.append(
            f'Slug contains uppercase: "{slug}". Use all-lowercase URLs.'
        )

    slug_lower = slug.lower()

    if "_" in slug_lower:
        issues.append(
            "Underscores in slug — use hyphens. "
            "Google treats hyphens as word separators."
        )

    if _SLUG_SAFE_RE.search(slug_lower):
        issues.append(
            "Slug contains special characters. "
            "Use only lowercase letters, numbers, and hyphens."
        )

    all_slug_words: list[str] = []
    for seg in segments:
        all_slug_words.extend(seg.split("-"))
    found_stop = [w for w in all_slug_words if w in _SLUG_STOP_WORDS]
    if found_stop:
        issues.append(
            f"Stop words in slug: {found_stop}. Remove unnecessary stop words."
        )

    word_counts: dict[str, int] = {}
    for word in all_slug_words:
        if len(word) > 2:
            word_counts[word] = word_counts.get(word, 0) + 1
    repeated = [w for w, c in word_counts.items() if c > 1]
    if repeated:
        issues.append(f"Repeated words in slug: {repeated}.")

    long_segments = [s for s in segments if len(s) > 60]
    if long_segments:
        issues.append(f"Slug segment(s) too long (> 60 chars): {long_segments}.")

    if keyword:
        kw_lower = keyword.lower().strip()
        kw_words = [w for w in kw_lower.split() if w not in _STOP_WORDS]
        full_match = (
            kw_lower.replace(" ", "-") in slug_lower or kw_lower in slug_lower
        )
        partial_match = not full_match and any(w in slug_lower for w in kw_words)

        if full_match:
            keyword_match = "full"
            notes.append(f'Primary keyword "{keyword}" found in slug.')
        elif partial_match:
            keyword_match = "partial"
            llm_review_required = True
            issues.append(
                f'Partial match for "{keyword}" in slug: "{slug}". '
                "LLM review: does slug reflect primary intent? "
                "Best practice: /category/primary-keyword."
            )
        else:
            keyword_match = "none"
            llm_review_required = True
            issues.append(
                f'Primary keyword "{keyword}" not in slug: "{slug}". '
                "Recommended: /category/primary-keyword."
            )
    else:
        llm_review_required = True
        notes.append(
            "No --keyword provided. LLM review: slug should contain primary keyword."
        )

    status = "warn" if issues else "pass"
    return {
        "status": status,
        "slug": slug,
        "is_homepage": False,
        "keyword_match": keyword_match,
        "llm_review_required": llm_review_required,
        "detail": " | ".join(issues + notes),
    }


def _build_summary(output: dict[str, Any]) -> dict[str, Any]:
    check_keys = ("url_slug", "title", "meta_description", "h1", "canonical")
    statuses = {k: output[k]["status"] for k in check_keys if k in output}
    overall = "pass"
    if any(s == "fail" for s in statuses.values()):
        overall = "fail"
    elif any(s == "warn" for s in statuses.values()):
        overall = "warn"

    llm_flags = [
        k
        for k in check_keys
        if k in output and output[k].get("llm_review_required")
    ]
    return {
        "overall": overall,
        "checks": statuses,
        "llm_review_required": bool(llm_flags),
        "llm_review_fields": llm_flags,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run page-level SEO checks (H1, title, meta description, "
            "canonical, URL slug) and output JSON."
        ),
    )
    parser.add_argument("url", help="Target page URL")
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=20,
        help="Request timeout in seconds",
    )
    parser.add_argument(
        "--keyword",
        "-k",
        help="Primary keyword to verify in H1, title, meta, and slug",
    )
    parser.add_argument(
        "--defaults",
        type=Path,
        default=None,
        help="TD length JSON (default: td_check_defaults.json)",
    )
    args = parser.parse_args()

    url = args.url
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    title_range, desc_range = _load_td_ranges(args.defaults)

    status_code, content, final_url, redirect_chain, error = _fetch(
        url,
        args.timeout,
    )

    base_result: dict[str, Any] = {
        "url": url,
        "final_url": final_url,
        "http_status": status_code,
        "redirect_chain": redirect_chain,
        "thresholds": {
            "title_length": list(title_range),
            "meta_description_length": list(desc_range),
        },
    }

    if error:
        base_result["error"] = error
        print(json.dumps(base_result, indent=2, ensure_ascii=False))
        sys.exit(1)

    if status_code != 200:
        base_result["error"] = (
            f"Page returned HTTP {status_code} — cannot perform on-page checks."
        )
        print(json.dumps(base_result, indent=2, ensure_ascii=False))
        sys.exit(1)

    if not content:
        base_result["error"] = "Page returned empty body."
        print(json.dumps(base_result, indent=2, ensure_ascii=False))
        sys.exit(1)

    seo_parser = _SEOParser()
    seo_parser.feed(content)

    output: dict[str, Any] = {
        **base_result,
        "url_slug": _check_url_slug(final_url, keyword=args.keyword),
        "title": _check_title(
            seo_parser.title,
            keyword=args.keyword,
            title_range=title_range,
        ),
        "meta_description": _check_meta_description(
            seo_parser.meta_description,
            keyword=args.keyword,
            desc_range=desc_range,
        ),
        "h1": _check_h1(seo_parser.h1_values, keyword=args.keyword),
        "canonical": _check_canonical(seo_parser.canonical, final_url),
    }
    output["summary"] = _build_summary(output)

    print(json.dumps(output, indent=2, ensure_ascii=False))

    has_failure = output["summary"]["overall"] == "fail"
    sys.exit(1 if has_failure else 0)


if __name__ == "__main__":
    main()
