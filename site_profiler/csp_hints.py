"""Extract CSP allowlist hints — vendors *potentially used*, not necessarily active."""
from __future__ import annotations

from .schema import CSPHints

_CAPTCHA = {
    "recaptcha": ["recaptcha", "google.com/recaptcha", "gstatic.com/recaptcha"],
    "hcaptcha": ["hcaptcha"],
    "turnstile": ["challenges.cloudflare.com/turnstile", "challenges.cloudflare.com"],
    "arkose": ["arkoselabs"],
    "geetest": ["geetest"],
    "datadome_captcha": ["captcha-delivery.com"],
    "aws_waf_captcha": ["awswaf.com"],
}

_CMS = {
    "contentful": ["ctfassets.net", "contentful.com"],
    "shopify": ["cdn.shopify.com", "shopify.com"],
    "wordpress": ["wp.com", "i0.wp.com"],
    "webflow": ["website-files.com", "webflow.com"],
    "hubspot": ["hubspot.com", "hs-banner.com", "hsappstatic.net"],
}

_BOT = {
    "perimeterx": ["px-cloud.net", "perimeterx.net", "px-cdn.net"],
    "datadome": ["datadome"],
    "akamai_bm": ["akstat.io", "akamaihd.net"],
}


def extract_csp_hints(csp: dict[str, list[str]]) -> CSPHints:
    if not csp:
        return CSPHints(raw_directives={})

    all_sources: set[str] = set()
    for sources in csp.values():
        for s in sources:
            all_sources.add(s.lower())
    csp_text = " ".join(all_sources)

    captcha_vendors = [v for v, pats in _CAPTCHA.items() if any(p in csp_text for p in pats)]
    cms_vendors = [v for v, pats in _CMS.items() if any(p in csp_text for p in pats)]
    bot_vendors = [v for v, pats in _BOT.items() if any(p in csp_text for p in pats)]

    return CSPHints(
        captcha_vendors=captcha_vendors,
        cms_vendors=cms_vendors,
        bot_protection_vendors=bot_vendors,
        raw_directives=csp,
    )
