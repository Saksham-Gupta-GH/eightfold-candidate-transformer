# Multi-Source Candidate Data Transformer

This project implements a robust candidate data transformer that merges multiple, messy data sources into a canonical profile and projects it using runtime configurations.

## Prerequisites

- Python 3.9+
- Virtual environment recommended.

```bash
# Set up a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install phonenumbers pydantic jsonschema jsonpath-ng pycountry requests python-dateutil
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
- **Extractors:** Found in `src/extractors.py`. Safely parses CSV and JSON into an unnormalized intermediate state.
- **Normalizers:** Found in `src/normalize.py`. Uses `phonenumbers` for E.164 and `pycountry` for ISO-3166 alpha-2 mapping.
- **Merge Engine:** Found in `src/merge.py`. Identity matching based on email, conflict resolution based on source confidence weights.
- **Projector:** Found in `src/projector.py`. Applies the JSON config at runtime using `jsonpath-ng` to reshape the final output.
