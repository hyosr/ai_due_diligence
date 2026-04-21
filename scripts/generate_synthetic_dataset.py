import json
import random
import numpy as np

np.random.seed(42)
random.seed(42)

def generate_service(index, risk_level):
    # Base commune
    service = {
        "service_name": f"{risk_level}_{index:03d}",
        "service_url": f"https://{risk_level.lower()}{index:03d}.example.com",
        "service_type": random.choice(["AI API", "SaaS", "Cloud Tool", "Other"]),
        "provider": random.choice(["SafeCorp", "MidTech", "RiskyAI", "TrustAI", "Unknown"]),
    }

    if risk_level == "LOW":
        service.update({
            "auth_method": random.choices(["oauth", "api_key"], weights=[0.7, 0.3])[0],
            "num_known_vulnerabilities": random.randint(0, 1),
            "encryption_present": True,
            "reputation_score_external": round(random.uniform(0.8, 1.0), 2),
            "blacklist_flag": False,
            "gdpr_compliant": random.choice([True, False]),
            "iso27001_compliant": random.choice([True, False]),
            "expected_risk_level": "LOW"
        })
    elif risk_level == "MEDIUM":
        service.update({
            "auth_method": random.choices(["api_key", "basic", "none"], weights=[0.5, 0.4, 0.1])[0],
            "num_known_vulnerabilities": random.randint(2, 4),
            "encryption_present": random.choice([True, False]),
            "reputation_score_external": round(random.uniform(0.4, 0.79), 2),
            "blacklist_flag": False,
            "gdpr_compliant": random.choice([True, False]),
            "iso27001_compliant": random.choice([True, False]),
            "expected_risk_level": "MEDIUM"
        })
    else:  # HIGH
        service.update({
            "auth_method": random.choices(["basic", "none"], weights=[0.6, 0.4])[0],
            "num_known_vulnerabilities": random.randint(5, 10),
            "encryption_present": False,
            "reputation_score_external": round(random.uniform(0.0, 0.39), 2),
            "blacklist_flag": random.choice([True, False]),
            "gdpr_compliant": False,
            "iso27001_compliant": False,
            "expected_risk_level": "HIGH"
        })
    return service

# Générer 100 exemples par classe (300 total)
dataset = []
for level in ["LOW", "MEDIUM", "HIGH"]:
    for i in range(1, 101):
        dataset.append(generate_service(i, level))

# Mélanger
random.shuffle(dataset)

# Sauvegarder
with open("scripts/synthetic_dataset_300.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print(f"Generated {len(dataset)} synthetic examples.")
