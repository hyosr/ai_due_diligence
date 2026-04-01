def compute_weighted_score(signal_results):
    total_weight = 0.0
    weighted_sum = 0.0
    explanations = []

    for s in signal_results:
        w = float(s.get("weight", 0.0))
        v = s.get("numeric_value", None)
        total_weight += w

        if v is None:
            contribution = w * 0.35
            reason = f"{s['key']}: unavailable data -> conservative contribution"
        else:
            v = max(0.0, min(1.0, float(v)))
            contribution = w * v
            reason = f"{s['key']}: normalized value={v:.2f}"

        weighted_sum += contribution
        explanations.append({
            "key": s["key"],
            "weight": round(w, 2),
            "numeric_value": None if s.get("numeric_value") is None else round(float(s["numeric_value"]), 3),
            "contribution": round(contribution, 3),
            "rationale": s.get("rationale", ""),
            "reason": reason
        })

    score = (weighted_sum / total_weight) * 100 if total_weight > 0 else 0.0
    return {"score": round(score, 2), "explanations": explanations}