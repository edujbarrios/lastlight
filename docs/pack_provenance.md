# Knowledge Pack Provenance

LastLight knowledge packs can carry provenance and freshness metadata in `lastlight-pack.json`. The metadata is informational and auditable; it is never executed.

Recommended manifest fields:

```json
{
  "name": "emergency-water-es",
  "version": "1.4.0",
  "languages": ["es"],
  "license": "CC-BY-4.0",
  "source": "https://example.org/source-guide",
  "publisher": "Example Relief Organization",
  "published_at": "2026-08-15",
  "expires_at": "2027-08-15",
  "provenance": [
    {
      "source": "https://example.org/source-guide",
      "publisher": "Example Relief Organization",
      "retrieved_at": "2026-08-16"
    }
  ]
}
```

## Verification model

`lastlight.provenance.verify_pack_provenance()` checks:

- ISO `published_at` and `expires_at` dates;
- future publication dates;
- expired packs;
- configurable age/freshness warnings;
- provenance-chain structure;
- deterministic SHA-256 pack fingerprints based on manifest metadata and document hashes;
- an optional declared `fingerprint_sha256` against the actual pack contents.

A stale pack produces a warning. An expired pack, invalid date, malformed provenance chain, or fingerprint mismatch is an error.

## Deterministic fingerprint

The fingerprint covers the normalized manifest (excluding the fingerprint field itself) plus the sorted path and SHA-256 digest of every Markdown document. This means a changed document, metadata field, or pack version produces a different fingerprint.

The fingerprint is designed to support future distribution catalogs without requiring LastLight itself to trust a network service. A catalog can publish pack metadata and expected fingerprints; LastLight can independently verify the downloaded artifact offline.

## Registry compatibility

This contract intentionally avoids depending on GitHub, a particular package registry, or a LastLight-operated service. A future public catalog only needs to distribute `.zip` packs and metadata that point to their source, publisher, version, dates, license, and expected SHA-256 fingerprint.

Cryptographic publisher signatures are deliberately not part of this first provenance layer. They can be added later as an optional stronger trust mechanism without changing the basic pack format.
