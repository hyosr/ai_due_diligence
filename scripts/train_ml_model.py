import argparse
import json
import joblib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score
from app.services.features import extract_features

LABEL_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

def vectorize_features(features_dict):
    feature_names = [
        "https_score", "ssl_valid_score", "auth_score", "vuln_score",
        "reputation_score", "compliance_score", "headers_score", "domain_age_risk"
    ]
    vec = []
    for name in feature_names:
        val = features_dict.get(name, 0.0)
        if val is None:
            val = 0.0
        vec.append(float(val))
    return np.array(vec)

def build_training_matrix(dataset):
    X, y = [], []
    for item in dataset:
        expected = item["expected_risk_level"].upper()
        payload = dict(item)
        payload.pop("expected_risk_level", None)
        collected = {"ssl_valid": payload.get("ssl_certificate_present", True)}
        feats = extract_features(payload, collected)
        X.append(vectorize_features(feats))
        y.append(LABEL_MAP[expected])
    return np.array(X, dtype=float), np.array(y, dtype=int)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--out", default="artifacts/risk_model.joblib")
    args = parser.parse_args()

    with open(args.dataset, "r", encoding="utf-8") as f:
        data = json.load(f)

    X, y = build_training_matrix(data)

    # Validation croisée 5-folds
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    model = RandomForestClassifier(n_estimators=300, max_depth=8, random_state=42, class_weight="balanced")
    
    y_pred = cross_val_predict(model, X, y, cv=cv)
    print("=== Cross-Validation (5 folds) ===")
    print(f"Accuracy: {accuracy_score(y, y_pred):.4f}")
    print(classification_report(y, y_pred, target_names=["LOW", "MEDIUM", "HIGH"]))

    # Entraînement final sur tout le dataset
    print("\n=== Training final model on full dataset ===")
    model.fit(X, y)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    joblib.dump(model, args.out)
    print(f"Model saved to {args.out}")

if __name__ == "__main__":
    main()



























# import argparse
# import json
# import joblib
# import os
# import sys
# from pathlib import Path

# # Ajouter le dossier racine du projet au chemin Python
# sys.path.insert(0, str(Path(__file__).parent.parent))

# import numpy as np
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import classification_report, accuracy_score

# from app.services.features import extract_features

# LABEL_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

# def vectorize_features(features_dict):
#     """Convertit un dictionnaire de features en vecteur numérique."""
#     # Définir l'ordre et les noms des features attendus
#     feature_names = [
#         "https_score", "ssl_valid_score", "auth_score", "vuln_score",
#         "reputation_score", "compliance_score", "headers_score", "domain_age_risk"
#     ]
#     vec = []
#     for name in feature_names:
#         val = features_dict.get(name, 0.0)
#         if val is None:
#             val = 0.0
#         vec.append(float(val))
#     return np.array(vec)

# def build_training_matrix(dataset):
#     X, y = [], []
#     for item in dataset:
#         expected = item["expected_risk_level"].upper()
#         payload = dict(item)
#         payload.pop("expected_risk_level", None)

#         # Simuler un objet collected minimal
#         collected = {
#             "ssl_valid": payload.get("ssl_certificate_present", True),
#         }

#         feats = extract_features(payload, collected)
#         X.append(vectorize_features(feats))
#         y.append(LABEL_MAP[expected])
#     return np.array(X, dtype=float), np.array(y, dtype=int)

# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--dataset", required=True)
#     parser.add_argument("--out", default="artifacts/risk_model.joblib")
#     args = parser.parse_args()

#     with open(args.dataset, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     X, y = build_training_matrix(data)

#     X_train, X_test, y_train, y_test = train_test_split(
#         X, y, test_size=0.25, random_state=42, stratify=y
#     )

#     model = RandomForestClassifier(
#         n_estimators=300,
#         max_depth=8,
#         random_state=42,
#         class_weight="balanced"
#     )
#     model.fit(X_train, y_train)

#     pred = model.predict(X_test)
#     print("Accuracy:", round(accuracy_score(y_test, pred), 4))
#     print(classification_report(y_test, pred, target_names=["LOW", "MEDIUM", "HIGH"]))

#     os.makedirs(os.path.dirname(args.out), exist_ok=True)
#     joblib.dump(model, args.out)
#     print(f"Saved model to: {args.out}")

# if __name__ == "__main__":
#     main()