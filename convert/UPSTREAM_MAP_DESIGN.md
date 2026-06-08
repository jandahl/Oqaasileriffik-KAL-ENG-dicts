# Standardized Upstream Source Map Design

## Purpose
This document specifies the standard output envelope for all data extraction pipelines across any cloned `Oqaasileriffik-*` repository. The goal is to provide a consistent intermediate representation ("Source Map") that extracts raw data exactly as it exists in the upstream source, before it is normalized or ingested into KalaalliCut.

## Envelope Schema

Every upstream pipeline must generate a JSON file containing the extracted data wrapped in the following standard envelope:

```json
{
  "meta": {
    "source_repo": "https://github.com/jandahl/Oqaasileriffik-...",
    "extraction_date": "2023-10-27T12:00:00Z",
    "available_fields": ["lexeme", "word_class", "gloss_en"]
  },
  "entries": [
    {
      "source_id": "unique identifier within the upstream",
      "raw_data": {
        "lexeme": "example_lexeme",
        "word_class": "example_class",
        "gloss_en": "example_gloss"
      }
    }
  ]
}
```

## Guidelines for Clone Implementations

1. **Exact Extraction:** The `raw_data` object should represent the data as faithfully to the source as possible. Do not force normalizations (like standardizing word classes or deducing valence) at this stage. 
2. **Explicit Fields List:** The `meta.available_fields` array must explicitly declare every field that is guaranteed to be extracted from this specific upstream source.
3. **Traceability:** The `source_id` must trace back unambiguously to the source artifact (e.g., spreadsheet row or SQL database primary key).
