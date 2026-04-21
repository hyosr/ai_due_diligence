
from typing import Dict, List

FEATURE_ORDER: List[str] = [
    "has_https",
    "ssl_valid",
    "encryption_present",
    "vulnerability_risk",
    "config_risk",
    "reputation_risk",
    "compliance_bonus",
    "weak_auth",
    "blacklist",
    "whitelist",
    "data_completeness_score",
    "headers_risk",
    "domain_age_risk",
]


# def vectorize_features(features: Dict) -> List[float]:
#     vec = []
#     for k in FEATURE_ORDER:
#         v = features.get(k, 0.0)
#         try:
#             vec.append(float(v))
#         except Exception:
#             vec.append(0.0)
#     return vec




import numpy as np

def vectorize_features(features_dict: dict) -> np.ndarray:
    """Convertit un dictionnaire de features en vecteur numérique."""
    # Ordre des features attendu par le modèle ML (à adapter selon votre modèle)
    feature_names = [
        "https_score",
        "ssl_valid_score",
        "auth_score",
        "vuln_score",
        "reputation_score",
        "compliance_score",
        "headers_score",
        "domain_age_risk"
    ]
    vec = []
    for name in feature_names:
        val = features_dict.get(name, 0.0)
        if val is None:
            val = 0.0
        vec.append(float(val))
    return np.array(vec)