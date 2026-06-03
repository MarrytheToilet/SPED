# SPED data layout

SPED now stores user-facing data by collection/theme.

```text
data/
  collections/
    <collection>/
      pdfs/                 # original PDFs selected in Web/CLI
      parsed/<paper_id>/    # MinerU output; full.md is the text entry point
      schemas/<slug>.json   # generated or uploaded schemas for this collection
      extracted/<slug>/     # extracted JSON records by schema and paper
        <paper_id>.json
  state/
    pdf_state.db            # upload/parse/extract job state
```

The default collection is configured by `DEFAULT_COLLECTION` in `.env`.

For the current project, the active collection is:

```text
data/collections/人工关节材料摩擦学/
```

## Directory Roles

- `pdfs/`
  - Raw PDF files.
  - Web cleanup deletes files here.

- `parsed/`
  - MinerU parsed outputs.
  - `full.md` is used by schema discovery and extraction.

- `schemas/`
  - Collection-local schema definitions.
  - A schema can be edited, cloned, deleted, or uploaded from Web.

- `extracted/<schema_slug>/`
  - Structured extraction results.
  - The data table and CSV/JSON export are built from these files.

- `state/pdf_state.db`
  - Runtime state for uploads, batches, parsed papers, and extraction status.
  - This is operational metadata, not the final structured dataset.

## Notes

Logical PDF names shown in the API/Web use:

```text
<collection>/<pdf filename>
```

The physical path is:

```text
data/collections/<collection>/pdfs/<pdf filename>
```
