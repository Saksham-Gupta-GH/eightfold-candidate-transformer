import csv
import json
import requests
from typing import List, Dict, Any
from .schema import CanonicalProfile, Provenance, Location, Links, Skill, Experience
from .normalize import normalize_phone, normalize_country, canonicalize_skill, normalize_date
import uuid
import sys

def generate_id():
    return str(uuid.uuid4())

class BaseExtractor:
    def extract(self, input_val: str) -> List[CanonicalProfile]:
        raise NotImplementedError

class CSVExtractor(BaseExtractor):
    """Extracts from Recruiter CSV: name, email, phone, current_company, title."""
    
    def extract(self, file_path: str) -> List[CanonicalProfile]:
        profiles = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        name = row.get('name', '').strip()
                        email = row.get('email', '').strip()
                        phone = row.get('phone', '').strip()
                        company = row.get('current_company', '').strip()
                        title = row.get('title', '').strip()
                        start_date = row.get('start_date', '').strip()
                        end_date = row.get('end_date', '').strip()
                        
                        norm_phone = normalize_phone(phone, default_region="IN") if phone.startswith(('9','8','7','6')) and len(phone) == 10 else normalize_phone(phone)
                        
                        experiences = []
                        if company or title:
                            experiences.append(Experience(
                                company=company if company else "Unknown",
                                title=title if title else "Unknown",
                                start=normalize_date(start_date),
                                end=normalize_date(end_date)
                            ))
                            
                        profile = CanonicalProfile(
                            candidate_id=generate_id(),
                            full_name=name if name else "",
                            emails=[email] if email else [],
                            phones=[norm_phone] if norm_phone else [],
                            experience=experiences,
                            overall_confidence=0.8
                        )
                        
                        if name:
                            profile.provenance.append(Provenance(field="full_name", source="CSV", method="csv_parser"))
                        if email:
                            profile.provenance.append(Provenance(field="emails", source="CSV", method="csv_parser"))
                        if norm_phone:
                            profile.provenance.append(Provenance(field="phones", source="CSV", method="normalized"))
                        if experiences:
                            profile.provenance.append(Provenance(field="experience", source="CSV", method="csv_parser"))
                            
                        profiles.append(profile)
                    except Exception as e:
                        print(f"Warning: Failed to parse row in CSV {file_path}. Error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Failed to open or read CSV {file_path}. Error: {e}", file=sys.stderr)
            
        return profiles

class GitHubExtractor(BaseExtractor):
    """Extracts unstructured data directly from a GitHub Profile URL."""
    
    def extract(self, url: str) -> List[CanonicalProfile]:
        profiles = []
        # Support both https://github.com/username and just username
        username = url.rstrip('/').split('/')[-1]
        
        api_url = f"https://api.github.com/users/{username}"
        try:
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 200:
                gh = resp.json()
                name = gh.get('name') or gh.get('login') or ""
                email = gh.get('email', '')
                bio = gh.get('bio', '')
                location_str = gh.get('location', '')
                profile_url = gh.get('html_url', url)
                
                norm_loc = None
                if location_str:
                    country = normalize_country(location_str)
                    if country:
                        norm_loc = Location(country=country)
                
                # Fetch repos to get languages as a proxy for skills
                skills = []
                repo_resp = requests.get(f"{api_url}/repos", timeout=10)
                if repo_resp.status_code == 200:
                    languages = set()
                    for r in repo_resp.json():
                        lang = r.get('language')
                        if lang: languages.add(lang)
                        
                    for lang in languages:
                        c_skill = canonicalize_skill(lang)
                        if c_skill:
                            skills.append(Skill(name=c_skill, confidence=0.9, sources=["GitHub API"]))
                
                profile = CanonicalProfile(
                    candidate_id=generate_id(),
                    full_name=name,
                    emails=[email] if email else [],
                    location=norm_loc,
                    links=Links(github=profile_url) if profile_url else None,
                    headline=bio if bio else None,
                    skills=skills,
                    overall_confidence=0.6
                )
                
                if name:
                    profile.provenance.append(Provenance(field="full_name", source="GitHub", method="github_api"))
                if email:
                    profile.provenance.append(Provenance(field="emails", source="GitHub", method="github_api"))
                if norm_loc:
                    profile.provenance.append(Provenance(field="location", source="GitHub", method="github_api_normalized"))
                if bio:
                    profile.provenance.append(Provenance(field="headline", source="GitHub", method="github_api"))
                if profile_url:
                    profile.provenance.append(Provenance(field="links", source="GitHub", method="github_api"))
                if skills:
                    profile.provenance.append(Provenance(field="skills", source="GitHub", method="repo_language_extraction"))
                    
                profiles.append(profile)
            else:
                print(f"Warning: GitHub API returned {resp.status_code} for {url}. Skipping.", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Failed to fetch GitHub profile {url}. Skipping. Error: {e}", file=sys.stderr)
            
        return profiles
