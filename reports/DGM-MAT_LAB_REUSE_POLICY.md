# DGM-MAT — Lab / Reuse Policy

Labs are the controlled experimental and reuse layer of the DGM-MAT ecosystem. They are not disposable and are not production authorities.

## Classes

1. DGM-MAT-Labs: official experimental satellite; prototypes and unstable research.
2. Independent Lab-* repositories: audited by actual content, not name.
3. Lab/experimental/prototype/sandbox directories inside other repositories: classified separately.

Independent Labs currently detected locally include:
- Lab-OllamaConection
- Lab-forge-icons
- Lab-ionicons.designerpack

Classification:
- CODE-LAB
- ASSET-LAB
- INTEGRATION-LAB
- RESEARCH-LAB
- ARCHIVE-LAB

## Promotion rule

Lab -> production is COPY/REFACTOR/PROMOTE, never a blind move.

Before promotion:
- verify license/source
- identify dependencies
- validate tests
- remove secrets and hardcoded credentials
- remove machine-specific paths
- define configuration
- define production owner
- define public contract
- preserve provenance
- run production validation

Reuse levels:
- L0 reference
- L1 asset
- L2 algorithm/pattern
- L3 isolated module
- L4 production component
- L5 architecture

L4/L5 require explicit validation.

## Lab-OllamaConection finding

Contains useful historical work around local Ollama HTTP, MCP-style HTTP, model routing, rate limiting and token/cost accounting.

It also contains obsolete/unsafe patterns including hardcoded localhost settings, placeholder API credentials, old model assumptions and duplicated server implementations.

It is therefore a reuse source, not a production dependency.

Potential destinations:
- DGM-MAT-Providers: provider adapters
- DGM-MAT-Connectors: local HTTP/MCP bridge
- DGM-Contracts: stable schemas
- Core: only through public contracts

## Isolation

Production must never import arbitrary working copies from Lab directories. Labs may consume stable public contracts, but must not become hidden Core dependencies.

DGM-MAT-FULL-MIRROR is not a Lab. It is a protected historical mirror and remains untouched.
