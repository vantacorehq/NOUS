# NOUS Ledger Protocol v1

One JSON object per line in `.nous/ledger.jsonl`.

| field | meaning |
|---|---|
| `unit` | first 16 hex of SHA-256 over the whitespace-normalized unit text |
| `key` | `path::name`, informational and used to detect drift |
| `who` | git email of the human who vouched |
| `claim` | their explanation, in their own words |
| `claim_hash` | SHA-256 of the lowercased, whitespace-collapsed claim (anti copy-paste) |
| `prev` | `hash` of the previous entry (64 zeros for the first) |
| `sig` | optional HMAC-SHA256 over the entry, key from `NOUS_KEY` |
| `hash` | SHA-256 over the canonical JSON of all other fields |

A unit is **lit** if any entry carries its `unit` id. **Drift** = an entry exists for its
`key` but not for its current id. **Dark** = neither. Coverage is weighted by non-blank LOC.

Interrogators: set `NOUS_JUDGE` to a command. It receives `{"code","claim"}` on stdin; exit 0 accepts.
