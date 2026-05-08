"""AWS WAF Captcha."""
from __future__ import annotations

from site_profiler.detectors.captcha.aws_waf_captcha import aws_waf_captcha
from tests.conftest import make_pair


def _detect(**kw):
    return aws_waf_captcha(make_pair(home_kwargs=kw))


def test_via_action_header():
    ev = _detect(headers={"x-amzn-waf-action": "captcha"})
    assert ev is not None
    assert ev.name == "aws_waf_captcha"


def test_via_script_host():
    ev = _detect(html='<script src="https://abc.captcha.awswaf.com/sdk.js"></script>')
    assert ev is not None


def test_via_render_call_in_body():
    ev = _detect(html='<script>CaptchaScript.renderCaptcha("#x", {});</script>')
    assert ev is not None


def test_no_action_no_evidence():
    ev = _detect(html="")
    assert ev is None
