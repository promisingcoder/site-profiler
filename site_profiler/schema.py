from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BlockStatus(str, Enum):
    NONE = "none"
    ARMED_PASSIVE = "armed_passive"
    SOFT_CHALLENGE = "soft_challenge"
    HARD_BLOCK = "hard_block"
    TLS_BLOCK = "tls_block"
    BODY_LIES = "body_lies"


class StrategyTier(str, Enum):
    API_DIRECT = "api_direct"
    HYDRATION_BLOB = "hydration_blob"
    STATIC_HTML = "static_html"
    HEADLESS_RENDER = "headless_render"
    HEADLESS_PLUS_EVASION = "headless_plus_evasion"
    UNKNOWN = "unknown"


class Variant(BaseModel):
    """A specific variant/sub-version of a detected technology.

    Examples: reCAPTCHA `v3` vs `v2_invisible` vs `enterprise`; Next.js
    `pages_router` vs `app_router`; Shopify `core` vs `hydrogen`.

    Variants do not stand alone — they live inside an Evidence object whose
    `name` identifies the parent technology. Strategy logic should keep
    keying on `Evidence.name` (the technology) and only branch on variants
    when the variant materially changes extraction approach.
    """
    model_config = ConfigDict(frozen=False)
    name: str                              # stable id, e.g. "v3", "app_router"
    label: str = ""                        # human label, e.g. "reCAPTCHA v3"
    confidence: float = Field(ge=0.0, le=1.0, default=0.9)
    markers: list[str] = Field(default_factory=list)
    version: Optional[str] = None
    extra: dict[str, str] = Field(default_factory=dict)


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=False)
    name: str
    detected: bool = True
    confidence: float = Field(ge=0.0, le=1.0)
    markers: list[str] = Field(default_factory=list)
    extra: dict[str, str] = Field(default_factory=dict)
    # Optional: captured version string ("13.4.0", "10.5", etc.)
    version: Optional[str] = None
    # Optional: variants matched within this technology (e.g. v2/v3 of reCAPTCHA).
    # Empty list = no sub-variant detection ran or no variant matched.
    variants: list[Variant] = Field(default_factory=list)


class Strategy(BaseModel):
    tier: StrategyTier
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class StructuredData(BaseModel):
    json_ld_present: bool = False
    json_ld_types: list[str] = Field(default_factory=list)
    opengraph: bool = False
    twitter_cards: bool = False
    microdata: bool = False
    microdata_types: list[str] = Field(default_factory=list)


class HydrationBlob(BaseModel):
    name: str
    size_bytes: int = 0
    sample: Optional[str] = None


class CSPHints(BaseModel):
    captcha_vendors: list[str] = Field(default_factory=list)
    cms_vendors: list[str] = Field(default_factory=list)
    bot_protection_vendors: list[str] = Field(default_factory=list)
    raw_directives: dict[str, list[str]] = Field(default_factory=dict)


class RobotsInfo(BaseModel):
    status: Optional[int] = None
    bytes: int = 0
    sitemap_urls: list[str] = Field(default_factory=list)
    crawl_delay: Optional[float] = None
    has_disallow_all: bool = False
    comments: list[str] = Field(default_factory=list)
    nonstandard_directives: dict[str, list[str]] = Field(default_factory=dict)


class Transport(BaseModel):
    status: Optional[int] = None
    redirect_chain: list[tuple[int, str]] = Field(default_factory=list)
    final_url: str = ""
    body_size_bytes: int = 0
    fetch_error: Optional[str] = None


class SiteProfile(BaseModel):
    request_url: str
    final_url: str
    fetched_at: datetime
    profiler_version: str = "0.1.0"
    transport: Transport
    edge: list[Evidence] = Field(default_factory=list)
    bot_protection: list[Evidence] = Field(default_factory=list)
    captcha: list[Evidence] = Field(default_factory=list)
    framework: list[Evidence] = Field(default_factory=list)
    hydration_blobs: list[HydrationBlob] = Field(default_factory=list)
    structured_data: StructuredData = Field(default_factory=StructuredData)
    csp_hints: CSPHints = Field(default_factory=CSPHints)
    robots: RobotsInfo = Field(default_factory=RobotsInfo)
    block_status: BlockStatus = BlockStatus.NONE
    block_evidence: list[str] = Field(default_factory=list)
    strategy: Strategy
