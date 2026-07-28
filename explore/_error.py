"""Explore Studio — Student API error types.

Defines ``StudentAPIError``, the exception raised for all predictable
student mistakes.  Internal engine failures are chained through this
type so developers can inspect the root cause while students see only
a friendly message.

Ownership: Student API team.
"""

from __future__ import annotations


class StudentAPIError(Exception):
    """Raised when a student makes a predictable mistake.

    The message uses conversational English suitable for beginners
    (ages 12+).  When wrapping an internal failure, use ::

        raise StudentAPIError("Friendly message") from original_exception

    so the original traceback is preserved for developers.
    """
