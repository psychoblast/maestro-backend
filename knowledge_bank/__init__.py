"""
PLMKR shared knowledge bank.

A read-only retrieval layer that lets ANY agent pull assembled expert knowledge
from ANY of the existing expert domains. The bank indexes knowledge that already
lives in this repository under ``skills/maestro-<slug>/knowledge/`` — it imports
nothing from outside the repo and assembles text exactly the way the per-agent
loaders already do.

Public surface:
- ``registry``: the data-driven domain catalog (``list_domains``, ``load_domain``)
- ``brain``:    deterministic routing + multi-domain consultation
- ``agent_home``: maps agent slugs to a home domain (paired vs. unpaired)
"""
