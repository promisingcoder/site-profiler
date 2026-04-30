"""site-profiler: URL -> structured SiteProfile."""
from .schema import (
    SiteProfile,
    Evidence,
    Strategy,
    StrategyTier,
    BlockStatus,
    StructuredData,
    HydrationBlob,
    CSPHints,
    RobotsInfo,
    Transport,
)
from .api import profile_url, profile_pair

__version__ = "0.1.0"
__all__ = [
    "profile_url",
    "profile_pair",
    "SiteProfile",
    "Evidence",
    "Strategy",
    "StrategyTier",
    "BlockStatus",
    "StructuredData",
    "HydrationBlob",
    "CSPHints",
    "RobotsInfo",
    "Transport",
    "__version__",
]
