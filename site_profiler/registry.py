"""Detector registry. Detectors register themselves via @register('category')."""
from __future__ import annotations
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .schema import Evidence, HydrationBlob
    from .parse import FetchedPair

DetectorFn = Callable[["FetchedPair"], "Optional[Evidence]"]
HydrationDetectorFn = Callable[["FetchedPair"], "list[HydrationBlob]"]

_REGISTRY: dict[str, list[DetectorFn]] = {}
_HYDRATION_REGISTRY: list[HydrationDetectorFn] = []


def register(category: str):
    """Decorator: register an Evidence-returning detector under a category."""
    def deco(fn: DetectorFn) -> DetectorFn:
        _REGISTRY.setdefault(category, []).append(fn)
        return fn
    return deco


def register_hydration(fn: HydrationDetectorFn) -> HydrationDetectorFn:
    """Decorator: register a HydrationBlob-list-returning detector."""
    _HYDRATION_REGISTRY.append(fn)
    return fn


def get_detectors(category: str) -> list[DetectorFn]:
    return list(_REGISTRY.get(category, []))


def all_categories() -> list[str]:
    return list(_REGISTRY.keys())


def get_hydration_detectors() -> list[HydrationDetectorFn]:
    return list(_HYDRATION_REGISTRY)
