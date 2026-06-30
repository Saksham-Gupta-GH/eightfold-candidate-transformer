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
            
        # Source reliability weights for fields (higher is better)
        field_priority = {
            "CSV": 0.9,     # High priority for contact info, work history
            "GitHub": 0.7   # High priority for code skills, medium for contact
        }
            
        base = group[0].model_copy()
        
        # Merge arrays using set logic for primitives
        all_emails = set(base.emails)
        all_phones = set(base.phones)
        
        total_conf = base.overall_confidence
        
        for other in group[1:]:
            all_emails.update(other.emails)
            all_phones.update(other.phones)
            
            # Simple field level resolution: we will take non-null fields
            # or override if the other source is inherently more reliable for that field.
            # E.g. we assume CSV is more reliable than GitHub for name/headline/location
            csv_wins = (base.overall_confidence < other.overall_confidence) 
            
            if other.full_name and (not base.full_name or csv_wins): base.full_name = other.full_name
            if other.headline and (not base.headline or csv_wins): base.headline = other.headline
            if other.location and (not base.location or csv_wins): base.location = other.location
                
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
                    for bs in base.skills:
                        if bs.name == s.name:
                            bs.confidence = min(1.0, bs.confidence + 0.1)
                            bs.sources.extend(s.sources)
                            bs.sources = list(set(bs.sources))
                            break

            # Experience - append
            base.experience.extend(other.experience)

            # Combine provenance
            base.provenance.extend(other.provenance)
            
            # Boost overall confidence slightly
            total_conf += (other.overall_confidence * 0.2)
            
        base.emails = list(all_emails)
        base.phones = list(all_phones)
        base.overall_confidence = min(1.0, total_conf)
        
        return base
