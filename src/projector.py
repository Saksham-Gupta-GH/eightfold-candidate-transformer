import jsonpath_ng.ext as jp
from typing import Dict, Any, List
from .schema import CanonicalProfile
from .normalize import normalize_phone, canonicalize_skill

class Projector:
    """Projects a CanonicalProfile into a custom schema based on a config."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fields = config.get("fields", [])
        self.include_confidence = config.get("include_confidence", True)
        self.include_provenance = config.get("include_provenance", True)
        self.on_missing = config.get("on_missing", "null") # 'null', 'omit', 'error'
        
    def project(self, profile: CanonicalProfile) -> Dict[str, Any]:
        output = {}
        profile_dict = profile.model_dump()
        
        for field_config in self.fields:
            out_path = field_config["path"]
            type_val = field_config.get("type", "string")
            is_required = field_config.get("required", False)
            from_path = field_config.get("from", out_path)
            normalize = field_config.get("normalize")
            
            # Extract using JSONPath
            try:
                jsonpath_expr = jp.parse(from_path)
                matches = jsonpath_expr.find(profile_dict)
                if matches:
                    if len(matches) > 1 or "[]" in type_val:
                        val = [m.value for m in matches]
                    else:
                        val = matches[0].value
                else:
                    val = None
            except Exception:
                val = None
                
            # Handle normalization
            if val is not None and normalize:
                if normalize == "E164":
                    val = normalize_phone(val)
                elif normalize == "canonical":
                    if isinstance(val, list):
                        val = [canonicalize_skill(v) for v in val]
                    else:
                        val = canonicalize_skill(val)
            
            # Handle missing
            if val is None or val == [] or val == "":
                if is_required and self.on_missing == "error":
                    raise ValueError(f"Required field missing: {out_path} from {from_path}")
                elif self.on_missing == "omit":
                    continue
                else:
                    output[out_path] = None
            else:
                output[out_path] = val
                
        if self.include_confidence:
            output["overall_confidence"] = profile_dict.get("overall_confidence")
        if self.include_provenance:
            output["provenance"] = profile_dict.get("provenance")
            
        return output
