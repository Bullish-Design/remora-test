# Edge Investigation Notes (2026-03-15)

## Evidence collected

- `NodeStore` defines an `edges` table and `add_edge()` API.
- No runtime caller invokes `NodeStore.add_edge()`.
- Discovery/reconciliation writes `parent_id` on nodes, but does not persist edges.
- Web graph UI reads edges only from `/api/edges` (backed by DB `edges` table).
- Local DB state after demo run:
  - `nodes = 18`
  - `nodes_with_parent = 17`
  - `edges = 0`
  - `missing_parent_refs = 0`

## Conclusion

The runtime currently stores node hierarchy in `nodes.parent_id`, but does not materialize those relationships into `edges`. Since the dashboard loads edges from `/api/edges`, the graph renders with nodes but no links.

## Recommended implementation

1. In reconciliation/projection, upsert containment edges (`edge_type = "contains"`) from `parent_id`.
2. Optionally add AST-based call/reference edges later (`edge_type = "calls"` etc.).
3. Short-term UI/API fallback: synthesize containment edges from `parent_id` when `edges` is empty.
