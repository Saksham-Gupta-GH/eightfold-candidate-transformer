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
        
        final_output = []
        for p in merged_profiles:
            try:
                projected = projector.project(p)
                final_output.append(projected)
            except ValueError as e:
                print(f"Skipping profile {p.candidate_id}: {e}", file=sys.stderr)
    else:
        # Default output
        final_output = [p.model_dump() for p in merged_profiles]
        
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
            else:
                console.print("[green]✓[/green] Generated default canonical schema")
                
            console.print(f"\n[bold]Profiles Generated: {len(final_output)}[/bold]\n")
            
            console.print_json(data=final_output)
        except ImportError:
            # Fallback if rich is not installed
            print(json.dumps(final_output, indent=2))

if __name__ == "__main__":
    main()
