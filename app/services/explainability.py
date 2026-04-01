def build_summary(score: float, confidence: float, explanations: list[dict]) -> str:
    if score >= 80:
        level = "High credibility"
    elif score >= 60:
        level = "Moderate credibility"
    elif score >= 40:
        level = "Low-to-moderate credibility"
    else:
        level = "Low credibility"

    top_positive = sorted(
        [e for e in explanations if (e.get("numeric_value") or 0) >= 0.7],
        key=lambda x: x["contribution"],
        reverse=True
    )[:2]
    top_negative = sorted(
        [e for e in explanations if (e.get("numeric_value") is not None and e.get("numeric_value") < 0.5)],
        key=lambda x: x["contribution"]
    )[:2]

    positives = ", ".join([p["key"] for p in top_positive]) if top_positive else "none"
    negatives = ", ".join([n["key"] for n in top_negative]) if top_negative else "none"

    return (
        f"{level}. Score={score}/100 with confidence={confidence}%. "
        f"Main strengths: {positives}. Main risks: {negatives}."
    )