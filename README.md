# Multi-Source Candidate Data Transformer

This project implements a robust candidate data transformer that merges multiple, messy data sources into a canonical profile and projects it using runtime configurations.

## Prerequisites

- Python 3.9+
- Virtual environment recommended.

```bash
# Set up a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Architecture

```text
    [CSV]               [GitHub Profile URL]
      |                           |
      v                           v
  [CSV Extractor]         [GitHub Extractor]
      |                           |
      +------------+--------------+
                   |
                   v
             [Normalizer] (Phones, Dates, Skills)
                   |
                   v
            [Merge Engine] (Source Priority & Confidence)
                   |
                   v
          [Canonical Profile]
                   |
                   v
             [Projector] <--- (custom_config.json)
                   |
                   v
              [JSON Output]
```

## How to Run

You can run the engine via the command line interface `main.py`. Provide at least one source file (`--csv` or `--github-url`), and optionally a config file (`--config`) to reshape the output.

### 1. Default Canonical Output
To run the pipeline and see the raw canonical profile with default schema:
```bash
python3 main.py --csv sample.csv --github-url https://github.com/torvalds
```

### 2. Custom Output Projection
To run the pipeline with a custom runtime config that reshapes fields, normalizes data, and filters based on rules:
```bash
python3 main.py --csv sample.csv --github-url https://github.com/torvalds --config custom_config.json
```

### 3. Save to file
To save the output to a JSON file rather than printing to stdout:
```bash
python3 main.py --csv sample.csv --github-url https://github.com/torvalds --config custom_config.json --out result.json
```

## Architecture Notes
- **Extractors:** Found in `src/extractors.py`. Safely parses CSV and JSON into an unnormalized intermediate state. Handles missing columns and API rate limits gracefully.
- **Normalizers:** Found in `src/normalize.py`. Uses `phonenumbers` for E.164, `pycountry` for ISO-3166 alpha-2 mapping, and `dateutil` for `YYYY-MM` parsing.
- **Merge Engine:** Found in `src/merge.py`. Identity matching based on email, conflict resolution based on source confidence weights.
- **Projector:** Found in `src/projector.py`. Applies the JSON config at runtime using `jsonpath-ng` to reshape the final output.

## Assumptions
- The GitHub REST API does not expose employment history (experience or education).
- Recruiter CSV data is considered highly authoritative for contact details and employment history.
- The default phone region is dynamically determined, but defaults to `IN` (India) for numbers starting with 9, 8, 7, 6 that are 10 digits long, otherwise falls back to standard parsing.
- Candidate identity mapping is heavily weighted on exact email matches.

## Limitations
- Candidate matching is currently email-first; if a candidate lacks an email in one source, they might not merge optimally.
- Resume (PDF) and LinkedIn extractors are not yet implemented for this iteration.
- Output validation is structurally guaranteed by Pydantic internals, but explicit runtime JSON schema validation on the projected output could be added for strict contract enforcement.

## Future Extensions
- **Resume PDF Parser**: Integrate a text extractor for unstructured resume data.
- **LinkedIn Integration**: Scrape or use the LinkedIn API to populate the `Experience` and `Education` schemas.
- **Fuzzy Identity Matching**: Use phonetic or string-distance algorithms to match candidates without email overlap.
- **Multiple Email Clustering**: Group disjoint profiles using a graph of overlapping identifiers.

## Testing
A small test suite is included to verify core functionalities like normalization and merge logic.
```bash
pytest tests/
```
