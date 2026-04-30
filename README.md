# site-profiler

URL → structured `SiteProfile`. Two HTTP requests (homepage + `/robots.txt`), no JS rendering, deterministic detectors with cited evidence.

## Install

```
pip install -e .
```

## Use

```python
from site_profiler import profile_url

profile = profile_url("https://www.allbirds.com/")
print(profile.model_dump_json(indent=2))
```

CLI:

```
python -m site_profiler https://www.allbirds.com/
```

## What it reports

- `transport`: status, redirect chain, body size
- `edge`: list of CDN/edge vendors detected with markers (Cloudflare, CloudFront, Akamai, Fastly, Vercel, Netlify)
- `bot_protection`: anti-bot vendors (Cloudflare BM, Akamai BM, DataDome, PerimeterX, AWS WAF, Kasada, first-party)
- `captcha`: captcha vendors loaded or allowlisted (reCAPTCHA, hCaptcha, Turnstile, Arkose, GeeTest, AWS WAF Captcha, DataDome Captcha)
- `framework`: site framework / CMS (Next.js Pages Router, Next.js App Router, Nuxt, Shopify (+Hydrogen/Oxygen), WordPress, Drupal, Webflow, Wix, Sphinx, Ghost, Salesforce PBC, HubSpot CMS)
- `hydration_blobs`: detected JSON state blobs (`__NEXT_DATA__`, `self.__next_f`, `__NUXT__`, `__INITIAL_STATE__`, `data-deferred-state`, `EAGER-DATA`, generic `app-context`)
- `structured_data`: JSON-LD types, OpenGraph, Twitter Cards, microdata
- `csp_hints`: vendors *allowlisted* in CSP (separate from "active on page")
- `robots`: parsed sitemap URLs, crawl-delay, disallow-all flag, comments, non-standard directives
- `block_status`: `none | armed_passive | soft_challenge | hard_block | tls_block | body_lies`
- `strategy`: first-guess extraction tier (`api_direct | hydration_blob | static_html | headless_render | headless_plus_evasion`) with confidence and evidence

Every detection emits `Evidence(name, confidence, markers)`.

## What it does NOT do

- No JS rendering (render-required is itself a reported signal)
- No anti-bot bypass (block status is reported, not defeated)
- No data extraction (profiling stops at "here's how I'd extract")
- No batch/async (use it from any caller; async upgrade is a future approach)
