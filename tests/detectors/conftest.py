"""Re-export ``make_pair`` so per-module tests can use the same builder
as the top-level test suite without each subdir reaching out and up."""
from tests.conftest import make_pair, make_page  # noqa: F401
