"""Rakshya: find personal information in Nepali, romanised Nepali and English text. See `runtime.py`."""
__version__ = "1.1.1"
__model__ = "1.1"   # the models that this code is released with

from .runtime import Rakshya  # noqa: E402

__all__ = ["Rakshya"]
