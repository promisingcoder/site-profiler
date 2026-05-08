"""ASP.NET / .NET (Microsoft) detector. ASP.NET classic and ASP.NET Core
share enough markers to live as variants on a single Evidence."""
from __future__ import annotations

import re

from ...parse import FetchedPair
from ...schema import Variant
from ..base import BaseMatch, Detector, VariantProbe


_VERSION_RE = re.compile(r"([\d]+\.[\d]+(?:\.[\d]+)?(?:\.[\d]+)?)")


class AspNetClassic(VariantProbe):
    name = "aspnet_classic"
    label = "ASP.NET (classic / Web Forms / MVC)"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        version: str | None = None

        v = pair.home.header("x-aspnet-version")
        if v:
            markers.append(f"x-aspnet-version: {v}")
            m = _VERSION_RE.search(v)
            if m:
                version = m.group(1)

        powered_by = pair.home.header("x-powered-by")
        if powered_by.lower().startswith("asp.net"):
            markers.append(f"x-powered-by: {powered_by}")

        body = pair.home.body_lower
        if 'name="__viewstate"' in body:
            markers.append("__VIEWSTATE form input (Web Forms)")
        for c in pair.home.set_cookie_names:
            if c.upper() in {"ASP.NET_SESSIONID", "ASPSESSIONID"} or c.startswith(".ASPXAUTH"):
                markers.append(f"cookie: {c}")

        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers, version=version)


class AspNetCore(VariantProbe):
    name = "aspnet_core"
    label = "ASP.NET Core"

    def probe(self, pair: FetchedPair) -> Variant | None:
        markers: list[str] = []
        for c in pair.home.set_cookie_names:
            if c.startswith(".AspNetCore"):
                markers.append(f"cookie: {c}")
        powered_by = pair.home.header("x-powered-by").lower()
        if "asp.net core" in powered_by or "asp.net" in powered_by and "core" in powered_by:
            markers.append(f"x-powered-by: {pair.home.header('x-powered-by')}")
        if not markers:
            return None
        return Variant(name=self.name, label=self.label, confidence=0.95, markers=markers)


class AspNet(Detector):
    name = "asp.net"
    category = "framework"
    base_confidence = 0.85
    variants = (AspNetClassic, AspNetCore)
    abstract = False

    def base_match(self, pair: FetchedPair) -> BaseMatch:
        markers: list[str] = []
        version: str | None = None

        if pair.home.header("x-aspnet-version"):
            v = pair.home.header("x-aspnet-version")
            markers.append(f"x-aspnet-version: {v}")
            m = _VERSION_RE.search(v)
            if m:
                version = m.group(1)

        powered_by = pair.home.header("x-powered-by")
        if powered_by.lower().startswith("asp.net"):
            markers.append(f"x-powered-by: {powered_by}")

        for c in pair.home.set_cookie_names:
            cu = c.upper()
            if (cu in {"ASP.NET_SESSIONID", "ASPSESSIONID"}
                or c.startswith(".ASPXAUTH")
                or c.startswith(".AspNetCore")):
                markers.append(f"cookie: {c}")

        body = pair.home.body_lower
        if 'name="__viewstate"' in body:
            markers.append("__VIEWSTATE form input")

        if not markers:
            return BaseMatch()
        return BaseMatch(markers=markers, version=version)
