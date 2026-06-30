# Multi-Source Candidate Data Transformer

This project implements a robust candidate data transformer that merges multiple, messy data sources into a canonical profile and projects it using runtime configurations.

## Prerequisites

- Python 3.9+
- Virtual environment recommended.

## How to Run

> [!TIP]
> The commands below use `python3` and `pip3`. If you are on Windows (or depending on your environment), you may need to use `python` and `pip` instead.

1. **Set up Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   *(Note: For Windows PowerShell, run `python -m venv venv` and `venv\Scripts\Activate.ps1`)*

2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Run the default pipeline (outputs full schema):**
   ```bash
   python3 main.py --csv sample.csv --github-url https://github.com/torvalds
   ```

4. **Run the projector pipeline (outputs flattened schema):**
   ```bash
   python3 main.py --csv sample.csv --github-url https://github.com/torvalds --config custom_config.json
   ```
   
5. **View the output as a Human-Readable Table (UI):**
   ```bash
   python3 main.py --csv sample.csv --github-url https://github.com/torvalds --config custom_config.json --format table
   ```

6. **Save to file (Optional):**
   ```bash
   python3 main.py --csv sample.csv --github-url https://github.com/torvalds --config custom_config.json --out result.json
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



## Architecture Notes
- **Extractors:** Found in `src/extractors.py`. Safely parses CSV and JSON into an unnormalized intermediate state. Handles missing columns and API rate limits gracefully.
- **Normalizers:** Found in `src/normalize.py`. Uses `phonenumbers` for E.164, `pycountry` for ISO-3166 alpha-2 mapping, and `dateutil` for `YYYY-MM` parsing.
- **Merge Engine:** Conflict resolution based on source-priority weighting with confidence-aware merging.
- **Projector:** Found in `src/projector.py`. Applies the JSON config at runtime using `jsonpath-ng` to reshape the final output.

## Assumptions
- The GitHub REST API does not expose employment history (experience or education).
- Recruiter CSV data is considered highly authoritative for contact details and employment history.
- The default phone region is dynamically determined, but defaults to `IN` (India) for numbers starting with 9, 8, 7, 6 that are 10 digits long, otherwise falls back to standard parsing.
- Candidate identity mapping uses exact email matches as the primary key, with a fallback to fuzzy `full_name` resolution to enable cross-source merging for candidates missing public emails (e.g. Linus Torvalds).

## Features
- **Dynamic JSON Schema Validation:** The pipeline mathematically generates a strict JSON Schema dynamically at runtime based on the user-provided `custom_config.json`, and explicitly validates all projected outputs before emitting them.
- **Derived Metrics:** The Merge Engine dynamically calculates `years_experience` by parsing and aggregating deduplicated `Experience` blocks.
- **Cross-Source Identity Resolution:** Automatically merges candidate profiles across structured and unstructured data using email and name resolution.

## Limitations
- Resume (PDF) and LinkedIn extractors are not yet implemented for this iteration.

## Future Extensions
- **Resume PDF Parser**: Integrate a text extractor for unstructured resume data.
- **LinkedIn Integration**: Scrape or use the LinkedIn API to populate the `Experience` and `Education` schemas.
- **Multiple Email Clustering**: Group disjoint profiles using a graph of overlapping identifiers.

## Sample Outputs
The generated JSON profiles for the provided sample inputs are committed in the repository for review:
- **Default Full Canonical Schema:** [`outputs/default_output.json`](outputs/default_output.json)
- **Custom Config Projected Schema:** [`outputs/custom_output.json`](outputs/custom_output.json)

## Testing
A small test suite is included to verify core functionalities like normalization and merge logic.
```bash
pytest tests/
```
