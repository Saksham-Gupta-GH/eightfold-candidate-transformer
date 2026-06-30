from typing import List, Dict, Optional
from .schema import CanonicalProfile, Skill

class MergeEngine:
    """Merges multiple CanonicalProfile records into unified profiles."""
    
    def merge(self, profiles: List[CanonicalProfile]) -> List[CanonicalProfile]:
        # Group by email. Candidates without an email are considered unique for simplicity here.
        grouped: Dict[str, List[CanonicalProfile]] = {}
        unique_profiles = []
        
        for p in profiles:
            if not p.emails:
                unique_profiles.append(p)
            else:
                for email in p.emails:
                    if email not in grouped:
                        grouped[email] = []
                    grouped[email].append(p)
                    
        # Process groups
        processed = set()
        for email, group in grouped.items():
            # If multiple emails map to same candidates, it gets tricky.
            # For simplicity, we just merge all profiles in this group.
            first_id = group[0].candidate_id
            if first_id in processed:
                continue
                
            merged = self._merge_group(group)
            unique_profiles.append(merged)
            
            for p in group:
                processed.add(p.candidate_id)
                
        return unique_profiles

    def _merge_group(self, group: List[CanonicalProfile]) -> CanonicalProfile:
        if len(group) == 1:
            return group[0]
            
        base = group[0].model_copy()
        
        # Merge arrays using set logic for primitives
        all_emails = set(base.emails)
        all_phones = set(base.phones)
        
        # We need to compute combined confidence and handle conflict resolution
        total_conf = base.overall_confidence
        
        for other in group[1:]:
            all_emails.update(other.emails)
            all_phones.update(other.phones)
            
            # For scalar fields like full_name or headline, we take the one from the source with higher confidence
            if other.overall_confidence > base.overall_confidence:
                if other.full_name: base.full_name = other.full_name
                if other.headline: base.headline = other.headline
                if other.location: base.location = other.location
                
            # Links
            if other.links:
                if not base.links:
                    base.links = other.links
                else:
                    if other.links.github: base.links.github = other.links.github
                    if other.links.linkedin: base.links.linkedin = other.links.linkedin
                    
            # Skills - combine and deduplicate
            existing_skill_names = {s.name for s in base.skills}
            for s in other.skills:
                if s.name not in existing_skill_names:
                    base.skills.append(s)
                    existing_skill_names.add(s.name)
                else:
                    # Boost confidence of existing skill if another source confirms it
                    for bs in base.skills:
                        if bs.name == s.name:
                            bs.confidence = min(1.0, bs.confidence + 0.1)
                            bs.sources.extend(s.sources)
                            bs.sources = list(set(bs.sources))
                            break

            # Combine provenance
            base.provenance.extend(other.provenance)
            
            # Boost overall confidence slightly because multiple sources matched this candidate
            total_conf += (other.overall_confidence * 0.2)
            
        base.emails = list(all_emails)
        base.phones = list(all_phones)
        base.overall_confidence = min(1.0, total_conf)
        
        return base
