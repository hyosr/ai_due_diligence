import argparse
import json
import copy
import requests
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix

LABEL_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
INV_LABEL = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}


def to_label(x: str) -> int:
    return LABEL_MAP.get((x or "").upper(), 1)


def classify(score: float, t_med: float, t_high: float) -> str:
    if score >= t_high:
        return "HIGH"
    if score >= t_med:
        return "MEDIUM"
    return "LOW"


def evaluate_thresholds(records, t_med, t_high):
    y_true, y_pred = [], []
    for rec in records:
        y_true.append(to_label(rec["expected_risk_level"]))
        y_pred.append(to_label(classify(rec["risk_score"], t_med, t_high)))

    acc = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average="macro")
    f1_high = f1_score(
        [1 if y == 2 else 0 for y in y_true],
        [1 if y == 2 else 0 for y in y_pred],
        zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])

    # false negative HIGH: true HIGH predicted not HIGH
    true_high = sum(1 for y in y_true if y == 2)
    fn_high = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 2 and yp != 2)
    fnr_high = (fn_high / true_high) if true_high > 0 else 0.0

    return {
        "threshold_medium": round(t_med, 3),
        "threshold_high": round(t_high, 3),
        "accuracy": round(acc, 4),
        "f1_macro": round(f1_macro, 4),
        "f1_high": round(f1_high, 4),
        "fnr_high": round(fnr_high, 4),
        "confusion_matrix": cm.tolist(),
    }


def collect_scores_from_api(dataset, base_url, headers):
    records = []

    for i, item in enumerate(dataset, start=1):
        payload = copy.deepcopy(item)
        expected = payload.pop("expected_risk_level")

        r1 = requests.post(f"{base_url}/assessment/service", headers=headers, json=payload, timeout=30)
        r1.raise_for_status()
        service_id = r1.json()["service_id"]

        r2 = requests.post(f"{base_url}/assessment/run/{service_id}", headers=headers, timeout=30)
        r2.raise_for_status()
        assessment_id = r2.json()["assessment_id"]

        final = None
        for _ in range(40):
            r3 = requests.get(f"{base_url}/assessment/{assessment_id}", headers=headers, timeout=30)
            r3.raise_for_status()
            final = r3.json()
            if final.get("status") in ("done", "failed"):
                break

        if final.get("status") != "done":
            print(f"[WARN] Assessment {assessment_id} not done. Skipping.")
            continue

        risk_score = float(final.get("risk_score", 0.5))
        records.append({
            "service_name": payload.get("service_name"),
            "expected_risk_level": expected,
            "risk_score": risk_score,
            "decision": final.get("decision"),
            "raw_predicted_level": final.get("risk_level"),
        })

        print(f"[{i}] {payload.get('service_name')} -> score={risk_score:.4f}, expected={expected}, api_level={final.get('risk_level')}")

    return records


def rank_results(results):
    # prioritize low false negative rate for HIGH, then f1_high, then macro f1, then accuracy
    return sorted(
        results,
        key=lambda x: (x["fnr_high"], -x["f1_high"], -x["f1_macro"], -x["accuracy"])
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="JSON dataset with expected_risk_level")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default="super-secret-key")
    parser.add_argument("--med-start", type=float, default=0.25)
    parser.add_argument("--med-end", type=float, default=0.60)
    parser.add_argument("--high-start", type=float, default=0.55)
    parser.add_argument("--high-end", type=float, default=0.90)
    parser.add_argument("--step", type=float, default=0.05)
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    with open(args.dataset, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    headers = {"Content-Type": "application/json", "x-api-key": args.api_key}
    records = collect_scores_from_api(dataset, args.base_url.rstrip("/"), headers)

    if not records:
        print("No records collected. Exiting.")
        return

    results = []
    t_med = args.med_start
    while t_med <= args.med_end + 1e-9:
        t_high = args.high_start
        while t_high <= args.high_end + 1e-9:
            if t_high > t_med:
                results.append(evaluate_thresholds(records, t_med, t_high))
            t_high += args.step
        t_med += args.step

    ranked = rank_results(results)
    top_k = ranked[: args.top_k]

    print("\n=== TOP CONFIGS ===")
    for i, r in enumerate(top_k, start=1):
        print(
            f"{i:02d}) med={r['threshold_medium']}, high={r['threshold_high']} | "
            f"acc={r['accuracy']} f1_macro={r['f1_macro']} f1_high={r['f1_high']} fnr_high={r['fnr_high']}"
        )

    best = top_k[0]
    print("\n=== RECOMMENDED (.env) ===")
    print(f"threshold_medium={best['threshold_medium']}")
    print(f"threshold_high={best['threshold_high']}")
    print(f"# metrics: acc={best['accuracy']} f1_macro={best['f1_macro']} f1_high={best['f1_high']} fnr_high={best['fnr_high']}")
    print(f"# confusion_matrix={best['confusion_matrix']}")

    with open("scripts/calibration_results.json", "w", encoding="utf-8") as f:
        json.dump({"records": records, "ranked_results": ranked}, f, indent=2)

    print("\nSaved full results to scripts/calibration_results.json")


if __name__ == "__main__":
    main()