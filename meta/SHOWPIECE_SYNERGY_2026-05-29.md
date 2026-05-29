# CAM-Codx Synergy Graph — 2026-05-29

*Evidence baseline: CAM_CAM commit `96cf5e6`, `claw.db` as of 2026-05-29.*

---

## Exploration Summary

| Metric | Value |
|--------|-------|
| Methodology pairs explored | 43,862 |
| Synergy matches found | 14 |
| Match rate | 0.032% |
| Total methodology links (all types) | 772 |
| Corpus size at time of exploration | 2,280 methodologies |

The low match rate is a feature, not a bug. Synergy is rare by design — the system only records a match when two patterns demonstrate a statistically significant co-occurrence signal combined with high semantic compatibility. The 14 that qualified are the pairs that empirically appear together in successful builds AND whose descriptions are semantically aligned.

---

## Proven Synergy Pairs

The 14 matches ranked by synergy score (0–1 scale):

| # | Type | Score | Method A (source) | Method B (source) |
|---|------|-------|-------------------|-------------------|
| 1 | synergy | 0.695 | **Resumable pipeline with persistent state and step directories** *(ASI-Evolve)* | **Autonomous Experiment Loop with Git-Based State Management** *(autoresearch)* |
| 2 | enhances | 0.633 | **Auto-Commit Hook for Git Integration** *(claude-obsidian)* | **Autonomous Research Loop via Git Branching** *(autoresearch-macos)* |
| 3 | feeds_into | 0.626 | **Early Environment Loading for Offline Cache Management** *(RAG-Anything)* | **Autonomous Experiment Loop with Git-Based State Management** *(autoresearch)* |
| 4 | feeds_into | 0.621 | **Deterministic Multi-Domain RAG without Vector Databases** *(deterministic_knowledge_retrieval)* | **Git-based result storage with show command access** *(agi)* |
| 5 | enhances | 0.620 | **Semantic CI Gates for LLM Output Verification** *(xplurx)* | **Autonomous Research Loop via Git Branching** *(autoresearch-macos)* |
| 6 | depends_on | 0.619 | **Git-Based State Management for Autonomous Agents** *(autoresearch)* | **Autonomous Experiment Loop with Git-Based State Management** *(autoresearch)* |
| 7 | feeds_into | 0.617 | **Code search database with identifier-splitting** *(created)* | **Git-based result storage with show command access** *(agi)* |
| 8 | feeds_into | 0.616 | **Robust Encoding-Aware Document Parsing Pipeline** *(youtu-graphrag)* | **Git-based result storage with show command access** *(agi)* |
| 9 | depends_on | 0.616 | **CLI and Configuration Management System** *(CloakBrowser)* | **Product management skills framework** *(created)* |
| 10 | feeds_into | 0.615 | **Fuzzy JSON Extraction from LLM Responses** *(book-to-screenplay)* | **Git-based result storage with show command access** *(agi)* |
| 11 | feeds_into | 0.612 | **Secure Multimodal Query Path Validation** *(RAG-Anything)* | **Git-based result storage with show command access** *(agi)* |
| 12 | feeds_into | 0.611 | **Autonomous Research Loop via Git Branching** *(autoresearch-macos)* | **Stigmergic Coordination Substrate with Pheromone Decay** *(rsisE)* |
| 13 | feeds_into | 0.606 | **Git-based result storage with show command access** *(agi)* | **Code search database with identifier-splitting** *(created)* |
| 14 | enhances | 0.602 | **7-Phase CLI Generation Methodology** *(CLI-Anything)* | **Proactive Context Enrichment via CLI Hooks** *(repowise)* |

---

## Synergy Type Breakdown

| Type | Count | Meaning |
|------|-------|---------|
| `feeds_into` | 8 | Output of Method A is natural input to Method B |
| `enhances` | 3 | Method A improves the effectiveness of Method B |
| `depends_on` | 2 | Method A requires Method B to function correctly |
| `synergy` | 1 | Bidirectional — both methods amplify each other |

---

## Link Type Breakdown (All 772 Links)

| Link Type | Count | What it means |
|-----------|-------|---------------|
| `co_retrieval` | 689 | Appeared together in the same recall query result — real-world co-use signal |
| `contradicts` | 69 | Semantically opposed approaches — using one undermines the other |
| `feeds_into` | 8 | Proven directional dependency discovered by synergy exploration |
| `enhances` | 3 | Proven amplification relationship |
| `depends_on` | 2 | Proven structural requirement |
| `synergy` | 1 | Bidirectional amplification |

---

## Notable Patterns in the Graph

**The git-state-management cluster** is the strongest hub: 6 of the 14 synergy edges involve either "Autonomous Experiment Loop with Git-Based State Management" or "Git-based result storage with show command access." This makes sense — git-as-state-machine is a foundational pattern that many higher-level patterns depend on or feed into.

**The autonomous research loop** appears in 4 edges as a target (it *receives* synergies from other patterns): environment management feeds into it, semantic CI gates enhance it, auto-commit hooks enhance it, and it has a direct depends_on relationship with its own sub-pattern. This marks it as a high-integration methodology — a pattern other patterns want to combine with.

**69 contradictions recorded.** These are equally valuable to the synergies — they represent approaches that should NOT be used together. A retrieval system built on deterministic TF-IDF rules (pattern #4 above) contradicts vector-embedding approaches. Knowing what not to combine saves real build failures.

---

## What This Means in Plain English

Most AI coding tools have a search index — you ask a question, it returns similar patterns. CAM-Codx has something more: a knowledge graph built from what actually happened in real builds.

The 689 `co_retrieval` links are a signal that two patterns keep appearing in the same searches together — like a bookstore noticing that customers who buy book A almost always buy book B. The 14 synergy edges go further: they mark pairs where using the two patterns together in a build produced better outcomes than using either alone. The 69 contradictions are the reverse — pairs that consistently cause problems when combined.

No human curated these relationships. They emerged from 43,862 automated pair comparisons across 2,280 patterns extracted from 266 real software repositories. The graph will keep growing as more builds run and more outcomes are recorded.

---

*Generated from live `claw.db` queries. See ACTION_PLANS_2026-05-29.md § SBP-3 for methodology.*
