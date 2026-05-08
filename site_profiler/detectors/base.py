"""Class-based detector framework.

Two styles coexist in this codebase, on purpose:

1. **Function-based** (legacy, still first-class): a free function decorated
   with ``@register("category")`` that takes a ``FetchedPair`` and returns
   ``Evidence | None``. Best for one-off detectors with quirky logic.

2. **Class-based** (this module): subclass ``Detector`` (or
   ``PatternDetector``), declare ``name``, ``category``, and either
   ``base_match`` or a list of declarative ``matchers``. Optionally declare
   ``variants`` (subclasses of ``VariantProbe``) and ``version_extractor``.
   The class auto-registers on subclass.

The class-based form is what you want when:
- a technology has multiple **variants** that change extraction strategy
  (reCAPTCHA v2 vs v3, Next.js Pages Router vs App Router, Shopify vs
  Hydrogen, GeeTest v3 vs v4),
- a technology has a **version** that we can capture from a header
  (``X-Powered-By: Next.js 13.4.0`` → ``version="13.4.0"``),
- you want declarative patterns (Wappalyzer-style) instead of imperative
  ``if`` blocks.

Both styles flow into the same ``site_profiler.registry._REGISTRY`` and are
run identically by ``aggregate.py``. There is no migration deadline.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar, Optional, Sequence

from ..parse import FetchedPair
from ..registry import register
from ..schema import Evidence, Variant


# ---------------------------------------------------------------------------
# Variant probes
# ---------------------------------------------------------------------------


class VariantProbe(ABC):
    """A specific sub-form a detector can take.

    Subclass and implement :meth:`probe`. The parent ``Detector`` instantiates
    each declared variant probe once and queries it after the base match
    succeeds. Multiple variants can match a single page (e.g. a Next.js page
    can simultaneously expose Pages Router data and App Router RSC streams,
    though that is unusual).
    """

    name: ClassVar[str] = ""
    label: ClassVar[str] = ""

    @abstractmethod
    def probe(self, pair: FetchedPair) -> Variant | None:
        """Return a Variant if matched, else None."""


# ---------------------------------------------------------------------------
# Pattern matchers (declarative)
# ---------------------------------------------------------------------------


class Matcher(ABC):
    """A declarative pattern run against a FetchedPair.

    A matcher returns:
      - a list of human-readable markers (one per match),
      - optionally a captured version string.

    Returning an empty marker list means "no match".
    """

    @abstractmethod
    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        ...


@dataclass(frozen=True)
class HeaderPattern(Matcher):
    """Match a response header.

    - ``pattern=None`` matches presence (any non-empty value).
    - ``pattern`` is a compiled regex; first capture group (if any) becomes
      the version when ``capture_version=True``.
    """
    name: str
    pattern: Optional[re.Pattern] = None
    capture_version: bool = False

    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        v = pair.home.header(self.name)
        if not v:
            return [], None
        if self.pattern is None:
            return [f"{self.name} header"], None
        m = self.pattern.search(v)
        if not m:
            return [], None
        version = None
        if self.capture_version and m.groups():
            version = m.group(1)
        return [f"{self.name}: {v}"], version


@dataclass(frozen=True)
class HeaderPrefixPattern(Matcher):
    """Match any header whose name starts with ``prefix`` (e.g. ``x-wf-``)."""
    prefix: str

    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        out: list[str] = []
        for h in pair.home.headers_lc:
            if h.startswith(self.prefix):
                out.append(f"{h} header")
        return out, None


@dataclass(frozen=True)
class ScriptSrcPattern(Matcher):
    """Match a ``<script src="...">`` whose URL contains ``substr`` (case-insensitive)."""
    substr: str
    pattern: Optional[re.Pattern] = None  # if set, overrides substr (also captures version via group 1)

    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        markers: list[str] = []
        version: Optional[str] = None
        for src in pair.home.script_srcs:
            sl = src.lower()
            if self.pattern is not None:
                m = self.pattern.search(src)
                if m:
                    markers.append(f"script src: {src}")
                    if version is None and m.groups():
                        version = m.group(1)
            elif self.substr.lower() in sl:
                markers.append(f"script src: {src}")
        # dedupe while preserving order
        return list(dict.fromkeys(markers)), version


@dataclass(frozen=True)
class ScriptHostPattern(Matcher):
    """Match the host of any ``<script src>`` against ``substr``."""
    substr: str

    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        out: list[str] = []
        s = self.substr.lower()
        for host in pair.home.script_src_hosts:
            if s in host.lower():
                out.append(f"script host: {host}")
        return out, None


@dataclass(frozen=True)
class CookiePattern(Matcher):
    """Match a Set-Cookie name. Either substring or regex.

    Cookie names beat headers for cross-tenant framework ID — the recon
    notes already cite this rule.
    """
    substr: str = ""
    pattern: Optional[re.Pattern] = None

    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        markers: list[str] = []
        names = pair.home.set_cookie_names + pair.robots.set_cookie_names
        for n in names:
            if self.pattern is not None:
                if self.pattern.search(n):
                    markers.append(f"cookie: {n}")
            elif self.substr and self.substr.lower() in n.lower():
                markers.append(f"cookie: {n}")
        return list(dict.fromkeys(markers)), None


@dataclass(frozen=True)
class BodySubstrPattern(Matcher):
    """Match a substring against the lowercased response body.

    For substrings that vary by case, pre-lowercase the substring you pass
    in. The body is already lowercased once at parse time, so this is
    essentially free.
    """
    substr: str
    min_count: int = 1

    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        body = pair.home.body_lower
        s = self.substr.lower()
        c = body.count(s)
        if c < self.min_count:
            return [], None
        if self.min_count > 1:
            return [f"{self.substr!r} x{c} in body"], None
        return [f"{self.substr!r} in body"], None


@dataclass(frozen=True)
class BodyRegexPattern(Matcher):
    """Run a regex over the response body. Captures version via group 1."""
    pattern: re.Pattern
    label: str = ""
    capture_version: bool = False

    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        body = pair.home.body_lower if self.pattern.flags & re.IGNORECASE else pair.home.html
        m = self.pattern.search(body)
        if not m:
            return [], None
        version = None
        if self.capture_version and m.groups():
            version = m.group(1)
        label = self.label or f"body match {self.pattern.pattern[:60]!r}"
        return [label], version


@dataclass(frozen=True)
class MetaGeneratorPattern(Matcher):
    """Match a ``<meta name="generator" content=...>`` value.

    ``capture_version=True`` pulls a version off the trailing portion using
    the regex's first capture group, e.g.
    ``re.compile(r"^WordPress\\s+([\\d.]+)", re.I)``.
    """
    pattern: re.Pattern
    capture_version: bool = False

    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        markers: list[str] = []
        version: Optional[str] = None
        for g in pair.home.meta_generators:
            m = self.pattern.search(g)
            if m:
                markers.append(f"meta generator: {g}")
                if version is None and self.capture_version and m.groups():
                    version = m.group(1)
        return list(dict.fromkeys(markers)), version


@dataclass(frozen=True)
class HtmlAttrPattern(Matcher):
    """Match an attribute on ``<html>`` or ``<body>``."""
    attr: str
    on: str = "either"  # "html" | "body" | "either"

    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        sources = []
        if self.on in ("html", "either"):
            sources.append(("<html>", pair.home.html_attrs))
        if self.on in ("body", "either"):
            sources.append(("<body>", pair.home.body_attrs))
        for tag, attrs in sources:
            if self.attr in attrs:
                return [f"{self.attr} on {tag}"], None
            for k in attrs:
                if k.startswith(self.attr):
                    return [f"{k} on {tag}"], None
        return [], None


@dataclass(frozen=True)
class CSPHostPattern(Matcher):
    """Match a CSP allowlist host. Note: this is "potentially uses", not
    "active on page" — pair this with a ScriptSrcPattern if you need
    confirmed loading."""
    substr: str

    def scan(self, pair: FetchedPair) -> tuple[list[str], Optional[str]]:
        markers: list[str] = []
        s = self.substr.lower()
        for directive, sources in pair.home.csp.items():
            for src in sources:
                if s in src.lower():
                    markers.append(f"csp {directive}: {src}")
        return list(dict.fromkeys(markers)), None


# ---------------------------------------------------------------------------
# Detector base class
# ---------------------------------------------------------------------------


@dataclass
class BaseMatch:
    """Result of a Detector's base match. ``markers=[]`` means no detection."""
    markers: list[str] = field(default_factory=list)
    extra: dict[str, str] = field(default_factory=dict)
    version: Optional[str] = None


class Detector(ABC):
    """Base for class-based detectors. Auto-registers concrete subclasses.

    Subclasses set ``name``, ``category``, optionally ``variants``, and
    implement either :meth:`base_match` (imperative) or set ``matchers``
    (declarative — see :class:`PatternDetector`).
    """

    name: ClassVar[str] = ""
    category: ClassVar[str] = ""
    variants: ClassVar[Sequence[type[VariantProbe]]] = ()
    base_confidence: ClassVar[float] = 0.9
    multi_marker_bonus: ClassVar[float] = 0.05  # added per extra marker, capped at 0.99
    abstract: ClassVar[bool] = True  # set False on concrete subclasses

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        # A class is abstract iff *its own* __dict__ sets abstract=True.
        # Concrete subclasses inherit `abstract` but don't redeclare it,
        # so they will register automatically. Intermediate base classes
        # (PatternDetector, etc.) explicitly redeclare abstract = True.
        if cls.__dict__.get("abstract", False):
            return
        if not cls.name or not cls.category:
            raise TypeError(
                f"Detector {cls.__name__} must set both name and category "
                f"(or set abstract = True)"
            )
        cls._register()

    @classmethod
    def _register(cls) -> None:
        instance = cls()

        def _runner(pair: FetchedPair) -> Evidence | None:
            return instance.detect(pair)

        _runner.__name__ = cls.name
        _runner.__qualname__ = f"{cls.__name__}.detect"
        cls._instance = instance     # type: ignore[attr-defined]
        cls._runner = _runner        # type: ignore[attr-defined]
        register(cls.category)(_runner)

    @abstractmethod
    def base_match(self, pair: FetchedPair) -> "BaseMatch":
        """Return a BaseMatch. Empty markers = no detection."""

    def detect(self, pair: FetchedPair) -> Evidence | None:
        result = self.base_match(pair)
        if not result.markers:
            return None

        # Compute confidence: base + bonus per extra marker, ceiling 0.99
        bonus = max(0, len(result.markers) - 1) * self.multi_marker_bonus
        confidence = min(0.99, self.base_confidence + bonus)

        version = result.version

        variants_found: list[Variant] = []
        for vp_cls in self.variants:
            try:
                v = vp_cls().probe(pair)
            except Exception as e:
                v = Variant(
                    name=f"_probe_error:{vp_cls.__name__}",
                    label=f"variant probe error",
                    confidence=0.0,
                    markers=[f"{type(e).__name__}: {e}"],
                )
            if v is not None:
                variants_found.append(v)

        if variants_found:
            confidence = max(confidence, max(v.confidence for v in variants_found))

        if version is None:
            for v in variants_found:
                if v.version:
                    version = v.version
                    break

        return Evidence(
            name=self.name,
            detected=True,
            confidence=confidence,
            markers=result.markers,
            extra=result.extra,
            version=version,
            variants=variants_found,
        )


# ---------------------------------------------------------------------------
# PatternDetector — declarative subclass
# ---------------------------------------------------------------------------


class PatternDetector(Detector):
    """Declarative detector — subclasses declare ``matchers``.

    ::

        class Astro(PatternDetector):
            name = "astro"
            category = "framework"
            matchers = [
                MetaGeneratorPattern(re.compile(r"^Astro\\s*v?([\\d.]+)?", re.I), capture_version=True),
                BodySubstrPattern("astro-island"),
                ScriptSrcPattern("/_astro/"),
            ]

    A version captured by *any* matcher becomes ``Evidence.version``.
    """

    abstract: ClassVar[bool] = True
    matchers: ClassVar[Sequence[Matcher]] = ()

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        markers: list[str] = []
        captured_version: Optional[str] = None
        for m in self.matchers:
            ms, ver = m.scan(pair)
            markers.extend(ms)
            if captured_version is None and ver:
                captured_version = ver
        markers = list(dict.fromkeys(markers))  # dedupe preserving order
        return BaseMatch(markers=markers, extra={}, version=captured_version)
