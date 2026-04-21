# ml/train_model.py
import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

# Charger votre dataset existant
dataset_path = "scripts/eval_dataset_30.json"
if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"Dataset non trouvé : {dataset_path}")

with open(dataset_path, "r") as f:
    data = json.load(f)

# Convertir en DataFrame
rows = []
for item in data:
    # Extraire les features (adaptez selon la structure de votre JSON)
    # Exemple générique – ajustez les noms de champs si nécessaire
    rows.append({
        "has_https": 1 if item.get("service_url", "").startswith("https") else 0,
        "ssl_valid": item.get("ssl_valid", 1),  # vous devrez peut-être l'extraire de raw_collection
        "auth_strength": {
            "oauth2": 0.9,
            "jwt": 0.8,
            "api_key": 0.6,
            "basic": 0.3,
            "none": 0.0
        }.get(item.get("auth_method", "none"), 0.5),
        "num_vulns": item.get("num_known_vulnerabilities", 0),
        "reputation": item.get("reputation_score_external", 0.5),
        "compliance_score": 0.9 if item.get("gdpr_compliant", False) else 0.3,
        "risk": 0 if item.get("expected_risk_level") == "LOW" else (1 if item.get("expected_risk_level") == "HIGH" else 0.5)
    })

df = pd.DataFrame(rows)

# Nettoyer les valeurs manquantes
df = df.dropna()

# Features (X) et target (y)
feature_cols = ["has_https", "ssl_valid", "auth_strength", "num_vulns", "reputation", "compliance_score"]
X = df[feature_cols]
y = (df["risk"] >= 0.7).astype(int)  # binaire : 1 = HIGH, 0 = LOW/MEDIUM (ou ajustez)

# Split pour validation
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Modèle
model = LogisticRegression(C=1.0, class_weight="balanced")
model.fit(X_train_scaled, y_train)

# Évaluation rapide
accuracy = model.score(X_test_scaled, y_test)
print(f"Accuracy sur test : {accuracy:.3f}")

# Sauvegarde
os.makedirs("ml", exist_ok=True)
joblib.dump(model, "ml/model.pkl")
joblib.dump(scaler, "ml/scaler.pkl")

print("✅ Modèle entraîné et sauvegardé dans ml/")