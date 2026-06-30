import argparse
import json
import sys
from src.extractors import CSVExtractor, GitHubExtractor
from src.merge import MergeEngine
from src.projector import Projector

def main():
    parser = argparse.ArgumentParser(description="Multi-Source Candidate Data Transformer")
    parser.add_argument("--csv", type=str, help="Path to Recruiter CSV file")
    parser.add_argument("--github-url", type=str, help="GitHub Profile URL (e.g. https://github.com/torvalds)")
    parser.add_argument("--config", type=str, help="Path to runtime configuration JSON")
    parser.add_argument("--out", type=str, help="Path to output JSON file (default stdout)")
    parser.add_argument("--format", type=str, choices=["json", "table"], default="json", help="Output format in terminal (json or table)")
    
    args = parser.parse_args()
    
    if not args.csv and not args.github_url:
        print("Error: Must provide at least one source (--csv or --github-url)")
        sys.exit(1)
        
    all_profiles = []
    
    if args.csv:
        extractor = CSVExtractor()
        all_profiles.extend(extractor.extract(args.csv))
        
    if args.github_url:
        extractor = GitHubExtractor()
        all_profiles.extend(extractor.extract(args.github_url))
        
    # Merge
    merger = MergeEngine()
    merged_profiles = merger.merge(all_profiles)
    
    # Project (if config provided)
    if args.config:
        with open(args.config, 'r') as f:
            config_data = json.load(f)
        projector = Projector(config_data)
        
        import jsonschema
        
        # Build dynamic schema for Stage 6 Validation
        dynamic_properties = {}
        dynamic_required = []
        for f_def in config_data.get("fields", []):
            dest = f_def["path"]
            dynamic_properties[dest] = {}
            if f_def.get("required", False):
                dynamic_required.append(dest)
                
        if config_data.get("include_confidence", True):
            dynamic_properties["overall_confidence"] = {"type": "number"}
        if config_data.get("include_provenance", True):
            dynamic_properties["provenance"] = {"type": "array"}
            
        dynamic_schema = {
            "type": "object",
            "properties": dynamic_properties,
            "required": dynamic_required
        }
        
        final_output = []
        for p in merged_profiles:
            try:
                projected = projector.project(p)
                # Stage 6: Validate projected output against dynamic schema
                jsonschema.validate(instance=projected, schema=dynamic_schema)
                final_output.append(projected)
            except ValueError as e:
                print(f"Skipping profile {p.candidate_id}: {e}", file=sys.stderr)
            except jsonschema.exceptions.ValidationError as e:
                print(f"Validation failed for profile {p.candidate_id}: {e.message}", file=sys.stderr)
    else:
        # Default output
        final_output = [p.model_dump() for p in merged_profiles]
        
        # Stage 6 Validation: Ensure the final output strictly adheres to the JSON Schema
        import jsonschema
        from src.schema import CanonicalProfile
        
        schema = CanonicalProfile.model_json_schema()
        for record in final_output:
            jsonschema.validate(instance=record, schema=schema)
        
    # Output
    if args.out:
        out_json = json.dumps(final_output, indent=2)
        with open(args.out, 'w') as f:
            f.write(out_json)
    else:
        try:
            from rich.console import Console
            from rich.panel import Panel
            
            console = Console()
            
            console.print(Panel("[bold cyan]Multi-Source Candidate Data Transformer[/bold cyan]", expand=False))
            
            if args.csv:
                console.print("[green]✓[/green] Loaded Recruiter CSV")
            if args.github_url:
                console.print("[green]✓[/green] Fetched GitHub Profile")
                
            console.print("[green]✓[/green] Normalized candidate data")
            console.print("[green]✓[/green] Merged records")
            
            if args.config:
                console.print("[green]✓[/green] Applied custom projection")
                console.print("[green]✓[/green] Validated output against dynamically generated JSON Schema")
            else:
                console.print("[green]✓[/green] Generated default canonical schema")
                console.print("[green]✓[/green] Validated output against strict JSON Schema")
                
            if args.format == "table":
                from rich.table import Table
                if final_output:
                    table = Table(show_header=True, header_style="bold magenta")
                    
                    # Dynamically add columns based on keys of the first profile
                    keys = list(final_output[0].keys())
                    for key in keys:
                        # Skip provenance in table view as it is too large
                        if key != "provenance":
                            table.add_column(key.replace("_", " ").title())
                            
                    for row in final_output:
                        row_values = []
                        for key in keys:
                            if key != "provenance":
                                val = row.get(key)
                                if isinstance(val, list):
                                    if val and isinstance(val[0], dict):
                                        val = f"[{len(val)} items]"
                                    else:
                                        val = ", ".join(str(v) for v in val) if val else "None"
                                elif isinstance(val, dict):
                                    val = "{...}"
                                elif val is None:
                                    val = "None"
                                else:
                                    # Round floats for cleaner display
                                    if isinstance(val, float):
                                        val = f"{val:.2f}"
                                row_values.append(str(val))
                        table.add_row(*row_values)
                    
                    console.print(table)
                else:
                    console.print("[yellow]No profiles generated.[/yellow]")
            else:
                console.print_json(data=final_output)
        except ImportError:
            # Fallback if rich is not installed
            print(json.dumps(final_output, indent=2))

if __name__ == "__main__":
    main()
