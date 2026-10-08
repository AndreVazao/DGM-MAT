# DGM-MAT Ecosystem Discovery & Reuse Intelligence

## Purpose

DGM-MAT must reuse existing work before creating a new capability. Ecosystem Discovery inventories approved local roots, identifies capability matches, ranks reuse candidates, and exposes overlap clusters.

## Safety boundary

Discovery is evidence collection only. It does not import, execute, activate, or make a runtime dependency on a discovered source.

The governed path remains:

REQUEST -> DISCOVER -> ASSESS -> SNAPSHOT -> SANDBOX -> ADAPT -> TEST -> REVIEW -> PROMOTE -> REGISTER -> ACTIVATE

## Scoring

Each candidate is ranked using:

- capability fit
- source trust/provenance
- adaptation cost
- source class

Local projects and DGM Labs receive higher trust than unproven external sources. External/credentialed sources remain subject to the existing approval gate.

## Overlap detection

Sources sharing the same inferred capability set are grouped into overlap clusters. This is an early anti-duplication signal, not an automatic merge/delete decision.

## Current implementation

- `core/organization/ecosystem_discovery.py`
- `core/organization/source_discovery.py`
- `core/organization/capability_models.py`
- `core/organization/recruitment.py`
- `core/organization/skill_forge.py`
- `tests/organization/test_ecosystem_discovery.py`

Validation: organization foundation + recruitment + ecosystem discovery tests pass (10 tests).

## Next integration boundary

The next safe integration is to let the Capability Scout worker produce a discovery report for a real CapabilityRequest and hand the selected candidate to the existing RecruitmentEngine/SkillForge pipeline. It must not auto-promote code.
