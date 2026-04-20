import argparse
import json
import os
import copy
import itertools
import requests
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix

LABEL_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def to_label(x: str) -> int:
    return LABEL_MAP.get((x or "").upper(), 1)


def classify(score: float, t_med: float, t_high: float) -> str:
    if score >= t_high:
        return "HIGH"
    if score >= t_med:
        return "MEDIUM"
    return "LOW"


def local_score(features: dict, wv: float, wc: float, wr: float) -> float:
    raw = (
        wv * float(features.get("vulnerability_risk", 0.0))
        + wc * float(features.get("config_risk", 0.0))
        + wr * float(features.get("reputation_risk", 0.0))
    )
    reduction = 0.10 * float(features.get("compliance_bonus", 0.0))
    return max(0.0, min(1.0, raw - reduction))


def evaluate(records, wv, wc, wr, t_med, t_high):
    y_true, y_pred = [], []

    for r in records:
        score = local_score(r["features"], wv, wc, wr)
        pred = classify(score, t_med, t_high)

        y_true.append(to_label(r["expected_risk_level"]))
        y_pred.append(to_label(pred))

    acc = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average="macro")
    f1_high = f1_score(
        [1 if y == 2 else 0 for y in y_true],
        [1 if y == 2 else 0 for y in y_pred],
        zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])

    true_high = sum(1 for y in y_true if y == 2)
    fn_high = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 2 and yp != 2)
    fnr_high = (fn_high / true_high) if true_high > 0 else 0.0

    return {
        "w_vulnerabilities": round(wv, 3),
        "w_config": round(wc, 3),
        "w_reputation": round(wr, 3),
        "threshold_medium": round(t_med, 3),
        "threshold_high": round(t_high, 3),
        "accuracy": round(acc, 4),
        "f1_macro": round(f1_macro, 4),
        "f1_high": round(f1_high, 4),
        "fnr_high": round(fnr_high, 4),
        "confusion_matrix": cm.tolist(),
    }


def rank_results(results):
    # Security-first ranking:
    # 1) Minimize false negatives on HIGH
    # 2) Maximize F1 HIGH
    # 3) Maximize macro F1
    # 4) Maximize accuracy
    return sorted(
        results,
        key=lambda x: (x["fnr_high"], -x["f1_high"], -x["f1_macro"], -x["accuracy"])
    )


def collect_features_from_api(dataset, base_url, headers):
    """
    Collect features once from API (/assessment/raw/{id}),
    then run fast local weight search without re-calling API each time.
    """
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

        if not final or final.get("status") != "done":
            print(f"[WARN] assessment_id={assessment_id} not done, skip")
            continue

        rr = requests.get(f"{base_url}/assessment/raw/{assessment_id}", headers=headers, timeout=30)
        rr.raise_for_status()
        raw = rr.json()

        feats = raw.get("features", {})
        records.append({
            "service_name": payload.get("service_name"),
            "expected_risk_level": expected,
            "features": feats
        })

        print(f"[{i}] collected features for {payload.get('service_name')}")

    return records


def generate_weight_grid(step=0.1):
    """
    Generates triples (wv,wc,wr) where wv+wc+wr=1.0
    """
    vals = [round(x, 3) for x in frange(0.1, 0.8, step)]
    triples = []
    for wv in vals:
        for wc in vals:
            wr = round(1.0 - wv - wc, 3)
            if wr < 0.1 or wr > 0.8:
                continue
            if abs((wv + wc + wr) - 1.0) < 1e-6:
                triples.append((wv, wc, wr))
    return triples


def frange(start, stop, step):
    x = start
    while x <= stop + 1e-9:
        yield x
        x += step


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="JSON dataset with expected_risk_level")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default="super-secret-key")
    parser.add_argument("--threshold-medium", type=float, default=None)
    parser.add_argument("--threshold-high", type=float, default=None)
    parser.add_argument("--weight-step", type=float, default=0.1)
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    t_med = args.threshold_medium if args.threshold_medium is not None else float(os.getenv("THRESHOLD_MEDIUM", 0.40))
    t_high = args.threshold_high if args.threshold_high is not None else float(os.getenv("THRESHOLD_HIGH", 0.70))

    with open(args.dataset, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    headers = {"Content-Type": "application/json", "x-api-key": args.api_key}
    records = collect_features_from_api(dataset, args.base_url.rstrip("/"), headers)

    if not records:
        print("No records with features collected.")
        return

    grid = generate_weight_grid(step=args.weight_step)
    print(f"\nTesting {len(grid)} weight combinations...")

    results = []
    for wv, wc, wr in grid:
        results.append(evaluate(records, wv, wc, wr, t_med, t_high))

    ranked = rank_results(results)
    top = ranked[: args.top_k]

    print("\n=== TOP WEIGHT CONFIGS ===")
    for i, r in enumerate(top, start=1):
        print(
            f"{i:02d}) wv={r['w_vulnerabilities']} wc={r['w_config']} wr={r['w_reputation']} | "
            f"acc={r['accuracy']} f1_macro={r['f1_macro']} f1_high={r['f1_high']} fnr_high={r['fnr_high']}"
        )

    best = top[0]
    print("\n=== RECOMMENDED .env ===")
    print(f"w_vulnerabilities={best['w_vulnerabilities']}")
    print(f"w_config={best['w_config']}")
    print(f"w_reputation={best['w_reputation']}")
    print(f"threshold_medium={best['threshold_medium']}")
    print(f"threshold_high={best['threshold_high']}")
    print(f"# metrics: acc={best['accuracy']} f1_macro={best['f1_macro']} f1_high={best['f1_high']} fnr_high={best['fnr_high']}")
    print(f"# confusion_matrix={best['confusion_matrix']}")

    with open("scripts/weight_calibration_results.json", "w", encoding="utf-8") as f:
        json.dump({"records": records, "ranked_results": ranked}, f, indent=2)

    print("\nSaved full results to scripts/weight_calibration_results.json")


if __name__ == "__main__":
    main()