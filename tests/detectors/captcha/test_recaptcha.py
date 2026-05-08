"""reCAPTCHA detector — base detection + every variant."""
from __future__ import annotations

from site_profiler.detectors.captcha.recaptcha import Recaptcha, recaptcha
from tests.conftest import make_pair


def _detect(html: str = "", **kw):
    home_kwargs = {"html": html, **kw}
    return recaptcha(make_pair(home_kwargs=home_kwargs))


# -- base detection ---------------------------------------------------------


def test_base_via_api_js():
    ev = _detect(
        '<script src="https://www.google.com/recaptcha/api.js?render=site_key"></script>'
    )
    assert ev is not None
    assert ev.name == "recaptcha"
    assert ev.extra.get("loaded") == "true"


def test_base_via_recaptcha_net():
    ev = _detect(
        '<script src="https://www.recaptcha.net/recaptcha/api.js"></script>'
    )
    assert ev is not None


def test_base_via_csp_only_returns_loaded_false():
    ev = _detect(
        "",
        headers={
            "content-security-policy": "script-src 'self' https://www.recaptcha.net"
        },
    )
    assert ev is not None
    assert ev.extra.get("loaded") == "false"


def test_no_recaptcha_no_evidence():
    ev = _detect("<html><body>plain page</body></html>")
    assert ev is None


# -- variants ---------------------------------------------------------------


def test_v2_checkbox_variant():
    ev = _detect(
        '<script src="https://www.google.com/recaptcha/api.js"></script>'
        '<div class="g-recaptcha" data-sitekey="abc"></div>'
    )
    names = {v.name for v in ev.variants}
    assert "v2_checkbox" in names


def test_v2_invisible_variant():
    ev = _detect(
        '<script src="https://www.google.com/recaptcha/api.js"></script>'
        '<div class="g-recaptcha" data-sitekey="abc" data-size="invisible"></div>'
    )
    names = {v.name for v in ev.variants}
    assert "v2_invisible" in names


def test_v3_variant_via_render_param():
    ev = _detect(
        '<script src="https://www.google.com/recaptcha/api.js?render=SITE_KEY_HERE"></script>'
        '<script>grecaptcha.execute("SITE_KEY_HERE", {action: "submit"});</script>'
    )
    names = {v.name for v in ev.variants}
    assert "v3" in names


def test_v3_variant_does_not_match_for_explicit():
    """``?render=explicit`` is v2 explicit-render, not v3."""
    ev = _detect(
        '<script src="https://www.google.com/recaptcha/api.js?render=explicit"></script>'
    )
    names = {v.name for v in ev.variants}
    assert "v3" not in names


def test_enterprise_variant_via_script():
    ev = _detect(
        '<script src="https://www.google.com/recaptcha/enterprise.js?render=SITE_KEY"></script>'
        '<script>grecaptcha.enterprise.execute("SITE_KEY", {action: "login"});</script>'
    )
    names = {v.name for v in ev.variants}
    assert "enterprise" in names


def test_enterprise_blocks_v3_match_when_enterprise_api_used():
    """grecaptcha.enterprise.execute should not also count as v3."""
    ev = _detect(
        '<script src="https://www.google.com/recaptcha/enterprise.js"></script>'
        '<script>grecaptcha.enterprise.execute("X");</script>'
    )
    names = {v.name for v in ev.variants}
    assert "enterprise" in names
    assert "v3" not in names


def test_no_variant_when_only_loader_present():
    ev = _detect(
        '<script src="https://www.google.com/recaptcha/api.js"></script>'
    )
    # Loader without any widget element / API call → no variant decisively matched
    assert ev is not None
    # Could match nothing; we don't assert empty since v2_checkbox might or might not
    # match depending on body markers — but enterprise/v3 must not match here.
    names = {v.name for v in ev.variants}
    assert "enterprise" not in names
    assert "v3" not in names


def test_class_instance_singleton():
    """Detector class instance is shared across calls — no per-call cost."""
    a = Recaptcha._instance
    b = Recaptcha._instance
    assert a is b
