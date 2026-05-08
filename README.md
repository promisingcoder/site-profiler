# site-profiler

URL → structured `SiteProfile`. Two HTTP requests (homepage + `/robots.txt`),
no JS rendering, deterministic detectors with cited evidence.

## Install

```
pip install -e .
# optional: MCP server entry point
pip install -e ".[mcp]"
```

## Use

### Library

```python
from site_profiler import profile_url

profile = profile_url("https://www.allbirds.com/")
print(profile.model_dump_json(indent=2))
```

### CLI

```
site-profiler https://www.allbirds.com/      # default: profile
site-profiler list-detectors                  # list every registered detector
site-profiler list-variants recaptcha         # show variants for one detector
site-profiler serve-mcp                       # run as an MCP server (stdio)
```

The CLI accepts `python -m site_profiler ...` interchangeably.

### MCP server

`site-profiler serve-mcp` exposes three tools over the Model Context Protocol:

- `profile_url(url, timeout?, user_agent?)` → JSON `SiteProfile`
- `list_detectors()` → grouped detector + variant list
- `list_variants(name)` → variants for a specific detector

Optional dep: install with `pip install site-profiler[mcp]`. Without it,
`serve-mcp` exits with a helpful install hint.

## What it reports

- `transport`: status, redirect chain, body size
- `edge`: CDN/edge vendors (Cloudflare, CloudFront, Akamai, Fastly, Vercel, Netlify)
- `bot_protection`: anti-bot vendors (Cloudflare BM, Akamai BM, DataDome, PerimeterX, AWS WAF, Kasada, first-party)
- `captcha`: captcha vendors loaded or allowlisted, with **variants** —
  reCAPTCHA (v2 checkbox / v2 invisible / v3 / Enterprise), hCaptcha
  (standard / invisible / enterprise), Turnstile (managed / non-interactive
  / invisible), GeeTest (v3 / v4), plus Arkose, AWS WAF, DataDome,
  Friendly Captcha
- `framework`: ~37 frameworks/CMS — Next.js (Pages Router / App Router /
  header-only variants), Nuxt, Shopify (core / Hydrogen / Oxygen variants),
  WordPress (with version), Drupal (with version), Astro, SvelteKit, Svelte,
  Remix, SolidStart, Qwik, Angular, AngularJS, Vue, React, Magento (1 / 2
  variants), Joomla, Squarespace, Laravel, Django, Rails, ASP.NET (classic /
  core variants), Express, Strapi, Sanity, Contentful, Bubble, Framer,
  Storyblok, plus the originals (Webflow, Wix, Sphinx, Ghost, Salesforce
  PBC, HubSpot, Gatsby)
- `hydration_blobs`: detected JSON state blobs (`__NEXT_DATA__`, `self.__next_f`, `__NUXT__`, `__INITIAL_STATE__`, `data-deferred-state`, `EAGER-DATA`, generic `app-context`)
- `structured_data`: JSON-LD types, OpenGraph, Twitter Cards, microdata
- `csp_hints`: vendors *allowlisted* in CSP (separate from "active on page")
- `robots`: parsed sitemap URLs, crawl-delay, disallow-all flag, comments, non-standard directives
- `block_status`: `none | armed_passive | soft_challenge | hard_block | tls_block | body_lies`
- `strategy`: first-guess extraction tier (`api_direct | hydration_blob | static_html | headless_render | headless_plus_evasion`) with confidence and evidence

Every detection emits `Evidence(name, confidence, markers, version?, variants[])`.

## Architecture: writing a new detector

Two equally first-class styles. Pick whichever fits your detector.

### Function-based — best for one-off logic

```python
# site_profiler/detectors/framework/mything.py
from ...registry import register
from ...schema import Evidence

@register("framework")
def mything(pair):
    if "x-mything" in pair.home.headers_lc:
        return Evidence(name="mything", confidence=0.9, markers=["x-mything header"])
    return None
```

Add `from . import mything` to the package `__init__.py`. Done.

### Class-based — best for variants and version capture

```python
# site_profiler/detectors/captcha/somecaptcha.py
from ...schema import Variant
from ..base import BaseMatch, Detector, VariantProbe

class SomeCaptchaInvisible(VariantProbe):
    name = "invisible"
    label = "SomeCaptcha (invisible)"
    def probe(self, pair):
        if 'data-mode="invisible"' in pair.home.body_lower:
            return Variant(name=self.name, label=self.label, confidence=0.95,
                           markers=['data-mode="invisible"'])
        return None

class SomeCaptcha(Detector):
    name = "somecaptcha"
    category = "captcha"
    base_confidence = 0.9
    variants = (SomeCaptchaInvisible,)
    abstract = False  # required to register

    def base_match(self, pair):
        if any("somecaptcha.io" in s for s in pair.home.script_srcs):
            return BaseMatch(markers=["somecaptcha.io script"])
        return BaseMatch()

# expose lowercase alias for direct testing / imports
somecaptcha = SomeCaptcha._runner
```

### Class-based with declarative patterns — Wappalyzer-style

```python
# site_profiler/detectors/framework/example.py
import re
from ..base import (
    PatternDetector, MetaGeneratorPattern, BodySubstrPattern, ScriptSrcPattern,
)

class Example(PatternDetector):
    name = "example"
    category = "framework"
    abstract = False
    matchers = (
        MetaGeneratorPattern(re.compile(r"^Example\s+v?([\d.]+)?", re.I), capture_version=True),
        BodySubstrPattern("example-island"),
        ScriptSrcPattern("/_example/"),
    )
```

The version captured by any matcher (via group 1 + `capture_version=True`)
is automatically promoted to `Evidence.version`.

Available matchers: `HeaderPattern`, `HeaderPrefixPattern`, `ScriptSrcPattern`,
`ScriptHostPattern`, `CookiePattern`, `BodySubstrPattern`, `BodyRegexPattern`,
`MetaGeneratorPattern`, `HtmlAttrPattern`, `CSPHostPattern`.

### Tests

Tests live under `tests/`. Per-detector tests go in
`tests/detectors/<category>/test_<name>.py` and use the shared
`make_pair` helper from `tests.conftest`. Adding a new detector means:
one source file under `site_profiler/detectors/<category>/`, one test
file under `tests/detectors/<category>/`, one import line in the
category `__init__.py`.

## What it does NOT do

- No JS rendering (render-required is itself a reported signal)
- No anti-bot bypass (block status is reported, not defeated)
- No data extraction (profiling stops at "here's how I'd extract")
- No batch/async (use it from any caller; async upgrade is a future approach)
