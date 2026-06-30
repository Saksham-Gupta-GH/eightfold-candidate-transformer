from typing import List, Dict, Optional
from .schema import CanonicalProfile, Skill

class MergeEngine:
    """Merges multiple CanonicalProfile records into unified profiles."""
    
    def merge(self, profiles: List[CanonicalProfile]) -> List[CanonicalProfile]:
        # Group by email, fallback to lowercase name. 
        grouped: Dict[str, List[CanonicalProfile]] = {}
        unique_profiles = []
        
        for p in profiles:
            key = None
            if p.emails:
                key = p.emails[0].lower()
            elif p.full_name:
                key = p.full_name.lower().strip()
                
            if not key:
                unique_profiles.append(p)
            else:
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(p)
                    
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
        
        # Helper to get the top priority source for a profile
        def get_top_source(profile: CanonicalProfile) -> str:
            # Simple heuristic: what's the primary source listed in provenance?
            if not profile.provenance:
                return "GitHub" # default fallback
            return profile.provenance[0].source
            
        base = group[0].model_copy()
        base_source = get_top_source(base)
        base_weight = field_priority.get(base_source, 0.5)
        
        # Merge arrays using set logic for primitives
        all_emails = set(base.emails)
        all_phones = set(base.phones)
        
        total_conf = base.overall_confidence
        
        for other in group[1:]:
            all_emails.update(other.emails)
            all_phones.update(other.phones)
            
            other_source = get_top_source(other)
            other_weight = field_priority.get(other_source, 0.5)
            
            # Field-level conflict resolution:
            # We override base fields if the other source has a higher priority weight.
            other_wins_priority = (base_weight < other_weight) 
            
            if other.full_name and (not base.full_name or other_wins_priority): base.full_name = other.full_name
            if other.headline and (not base.headline or other_wins_priority): base.headline = other.headline
            if other.location and (not base.location or other_wins_priority): base.location = other.location
                
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

            # Deduplicate experience
            seen_exp = set()
            dedup_exp = []
            for e in base.experience:
                key = (
                    e.company.lower().strip() if e.company else "", 
                    e.title.lower().strip() if e.title else "",
                    e.start.strip() if e.start else ""
                )
                if key not in seen_exp:
                    seen_exp.add(key)
                    dedup_exp.append(e)
            base.experience = dedup_exp
            
            # Combine provenance
            base.provenance.extend(other.provenance)
            
            # Deduplicate provenance
            seen_prov = set()
            dedup_prov = []
            for prov in base.provenance:
                key = (prov.field, prov.source, prov.method)
                if key not in seen_prov:
                    seen_prov.add(key)
                    dedup_prov.append(prov)
            base.provenance = dedup_prov
            
            # Boost overall confidence slightly
            total_conf += (other.overall_confidence * 0.2)
            
        base.emails = list(all_emails)
        base.phones = list(all_phones)
        base.overall_confidence = min(1.0, total_conf)
        
        # Calculate years_experience based on deduplicated experience
        from datetime import datetime
        total_months = 0
        for e in base.experience:
            try:
                start = datetime.strptime(e.start, "%Y-%m") if getattr(e, 'start', None) else None
                end = datetime.strptime(e.end, "%Y-%m") if getattr(e, 'end', None) else datetime.now()
                if start:
                    delta = end.year * 12 + end.month - (start.year * 12 + start.month)
                    if delta > 0:
                        total_months += delta
            except Exception:
                pass
                
        if total_months > 0:
            base.years_experience = round(total_months / 12, 1)
        
        return base
