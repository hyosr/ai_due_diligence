import argparse
import json
import requests
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

LABEL_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def to_label(x):
    return LABEL_MAP.get((x or "").upper(), 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default="super-secret-key")
    parser.add_argument("--dataset", required=True, help="Path to JSON file")
    args = parser.parse_args()

    headers = {"Content-Type": "application/json", "x-api-key": args.api_key}

    with open(args.dataset, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    y_true = []
    y_pred = []

    for i, item in enumerate(dataset, start=1):
        expected = item.pop("expected_risk_level")

        # create service
        r1 = requests.post(f"{args.base_url}/assessment/service", headers=headers, json=item, timeout=30)
        r1.raise_for_status()
        service_id = r1.json()["service_id"]

        # run assessment
        r2 = requests.post(f"{args.base_url}/assessment/run/{service_id}", headers=headers, timeout=30)
        r2.raise_for_status()
        assessment_id = r2.json()["assessment_id"]

        # poll
        final = None
        for _ in range(40):
            r3 = requests.get(f"{args.base_url}/assessment/{assessment_id}", headers=headers, timeout=30)
            r3.raise_for_status()
            final = r3.json()
            if final.get("status") in ("done", "failed"):
                break

        pred = final.get("risk_level", "MEDIUM")
        y_true.append(to_label(expected))
        y_pred.append(to_label(pred))
        print(f"[{i}] expected={expected} pred={pred} score={final.get('risk_score')} decision={final.get('decision')}")

    print("\nAccuracy:", round(accuracy_score(y_true, y_pred), 4))
    print("\nConfusion Matrix:\n", confusion_matrix(y_true, y_pred))
    print("\nClassification Report:\n", classification_report(y_true, y_pred, target_names=["LOW", "MEDIUM", "HIGH"]))


if __name__ == "__main__":
    main()