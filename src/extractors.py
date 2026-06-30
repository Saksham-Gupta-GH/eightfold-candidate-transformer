import csv
import json
from typing import List, Dict, Any
from .schema import CanonicalProfile, Provenance, Location, Links, Skill
from .normalize import normalize_phone, normalize_country, canonicalize_skill
import uuid

def generate_id():
    return str(uuid.uuid4())

class BaseExtractor:
    def extract(self, file_path: str) -> List[CanonicalProfile]:
        raise NotImplementedError

class CSVExtractor(BaseExtractor):
    """Extracts from Recruiter CSV: name, email, phone, current_company, title."""
    
    def extract(self, file_path: str) -> List[CanonicalProfile]:
        profiles = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic fields
                name = row.get('name', '').strip()
                email = row.get('email', '').strip()
                phone = row.get('phone', '').strip()
                
                # Normalization
                norm_phone = normalize_phone(phone)
                
                profile = CanonicalProfile(
                    candidate_id=generate_id(),
                    full_name=name,
                    emails=[email] if email else [],
                    phones=[norm_phone] if norm_phone else [],
                    overall_confidence=0.8  # Base confidence for Recruiter CSV
                )
                
                # Provenance tracking
                if email:
                    profile.provenance.append(Provenance(field="emails", source="CSV", method="direct"))
                if norm_phone:
                    profile.provenance.append(Provenance(field="phones", source="CSV", method="normalized"))
                if name:
                    profile.provenance.append(Provenance(field="full_name", source="CSV", method="direct"))
                    
                profiles.append(profile)
                
        return profiles

class GitHubExtractor(BaseExtractor):
    """Extracts from a GitHub JSON dump representing API response."""
    
    def extract(self, file_path: str) -> List[CanonicalProfile]:
        profiles = []
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Assume data is a list of profiles or a single profile
            if isinstance(data, dict):
                data = [data]
                
            for gh in data:
                name = gh.get('name', gh.get('login', ''))
                email = gh.get('email', '')
                bio = gh.get('bio', '')
                location_str = gh.get('location', '')
                url = gh.get('html_url', '')
                gh_skills = gh.get('languages', []) # simplified representation
                
                norm_loc = None
                if location_str:
                    country = normalize_country(location_str) # simplified, extracting country
                    if country:
                        norm_loc = Location(country=country)
                
                skills = []
                for s in gh_skills:
                    c_skill = canonicalize_skill(s)
                    if c_skill:
                        skills.append(Skill(name=c_skill, confidence=0.9, sources=["GitHub"]))
                        
                profile = CanonicalProfile(
                    candidate_id=generate_id(),
                    full_name=name,
                    emails=[email] if email else [],
                    location=norm_loc,
                    links=Links(github=url) if url else None,
                    headline=bio if bio else None,
                    skills=skills,
                    overall_confidence=0.6  # Unstructured/Scraped has lower base confidence
                )
                
                # Provenance
                if email:
                    profile.provenance.append(Provenance(field="emails", source="GitHub", method="direct"))
                if skills:
                    profile.provenance.append(Provenance(field="skills", source="GitHub", method="canonicalized"))
                    
                profiles.append(profile)
                
        return profiles
