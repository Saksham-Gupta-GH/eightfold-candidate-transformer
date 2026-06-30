import argparse
import json
import sys
from src.extractors import CSVExtractor, GitHubExtractor
from src.merge import MergeEngine
from src.projector import Projector

def main():
    parser = argparse.ArgumentParser(description="Multi-Source Candidate Data Transformer")
    parser.add_argument("--csv", type=str, help="Path to Recruiter CSV file")
    parser.add_argument("--github", type=str, help="Path to GitHub JSON dump file")
    parser.add_argument("--config", type=str, help="Path to runtime configuration JSON")
    parser.add_argument("--out", type=str, help="Path to output JSON file (default stdout)")
    
    args = parser.parse_args()
    
    if not args.csv and not args.github:
        print("Error: Must provide at least one source (--csv or --github)")
        sys.exit(1)
        
    all_profiles = []
    
    if args.csv:
        extractor = CSVExtractor()
        all_profiles.extend(extractor.extract(args.csv))
        
    if args.github:
        extractor = GitHubExtractor()
        all_profiles.extend(extractor.extract(args.github))
        
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
    out_json = json.dumps(final_output, indent=2)
    if args.out:
        with open(args.out, 'w') as f:
            f.write(out_json)
    else:
        print(out_json)

if __name__ == "__main__":
    main()
