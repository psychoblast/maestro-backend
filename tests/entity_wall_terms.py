"""
Entity-wall forbidden terms — encoded fixture for test hygiene.

WHY THIS FILE EXISTS
--------------------
The A&R pilot tests must assert that assembled prompts, JSON responses, and
rendered HTML never leak provenance markers from the knowledge base's prior
home. Hardcoding those markers as plaintext assertion lists would re-introduce
the very strings we are trying to keep out of this repository.

So the forbidden terms are stored base64-encoded and decoded at runtime. No
provenance marker appears as plaintext in source.

SCOPE — PROVENANCE MARKERS ONLY
-------------------------------
FORBIDDEN_TERMS contains ONLY true provenance markers: the prior toolchain name
("[scrubbed]" / "[scrubbed]"), the prior owning entity ("[scrubbed]" /
"[scrubbed]"), and the scrubbed rubric codenames.

It deliberately does NOT contain sibling product names. Those are not
provenance — they must not live in this repository at all, in any form,
encoded or otherwise. They are therefore neither stored nor checked here.
"""
import base64

# Each entry is the base64 encoding of a lowercased provenance marker.
# Decoded at import time into FORBIDDEN_TERMS. Keeping the plaintext out of
# source is the entire point of this file — do not inline decoded values.
_ENCODED_FORBIDDEN_TERMS = (
    "YWdlbnQtb3M=",          # prior toolchain (hyphenated)
    "YWdlbnRvcw==",          # prior toolchain (concatenated)
    "bWluZHZpc2lvbg==",      # prior owning entity
    "bWluZHZpc2lvbmxsYw==",  # prior owning entity (with corp suffix)
    "bWluZCB2aXNpb24=",      # prior owning entity (spaced variant)
    "bmV4dXMtb3ZlcnJpZGU=",  # scrubbed rubric codename
    "Z2F0ZS1ldmlkZW5jZQ==",  # scrubbed rubric codename
)

# Lowercased provenance markers, decoded at runtime.
FORBIDDEN_TERMS = tuple(
    base64.b64decode(_enc).decode("utf-8").lower()
    for _enc in _ENCODED_FORBIDDEN_TERMS
)


def assert_no_forbidden_terms(text: str) -> None:
    """Raise AssertionError if any forbidden provenance marker appears in ``text``.

    Matching is case-insensitive: ``text`` is lowercased before comparison and
    every entry in FORBIDDEN_TERMS is already lowercased.
    """
    haystack = (text or "").lower()
    for term in FORBIDDEN_TERMS:
        assert term not in haystack, (
            f"Forbidden provenance marker found in text. "
            "Run the entity gate before committing."
        )
