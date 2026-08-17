# CAM_Codx knowledge-graph route

Normal user language is:

> Use CAM_Codx to assess the impact of `<named change or symbol>`.

CAM_Codx selects the read-only `knowledge-graph-query` manager packet. The
packet calls CAM_CAM's hidden `knowledge-graph-query` troubleshooting surface
with a fixed list-form argv, a named existing database, an immutable snapshot
ID, and a canonical seed node. It returns a compact, receipt-backed graph
context suitable for planning.

The route is read-only and requires no product approval. It does not scan a
live corpus, create a graph snapshot, call a provider, load a model, mutate a
target, or change configuration. Association-only edges are omitted by
default; an explicit troubleshooting request may opt them in, but they remain
non-factual evidence.

Every result is bounded to two hops by default, with edge-type, degree, node,
edge, and token limits. A stale source revision, missing receipt, unknown
snapshot/seed, missing database, or budget overrun fails closed. Direct CAM_CAM
use remains for runtime development, recovery, and regression isolation; it is
not the normal general-purpose router.

This is a fixture/local-snapshot integration surface, not proof of live CAM
accuracy or production acceptance. Live ingestion and any future provider or
model-assisted entity resolution require separate contracts and approvals.
