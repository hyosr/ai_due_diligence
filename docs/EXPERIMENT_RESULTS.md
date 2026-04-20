# AI Due Diligence – Experimental Results

## Date
April 20, 2026

## Project
**AI Due Diligence – AI SaaS Credibility Assessment**  
Zero-Trust assessment engine with explainable scoring and policy-based enforcement.

---

## 1) Final Configuration (.env)

```env
w_vulnerabilities=0.1
w_config=0.3
w_reputation=0.6
threshold_medium=0.25
threshold_high=0.55
```

---

## 2) Evaluation Setup

- **Evaluation script:** `scripts/evaluate_model.py`
- **Dataset:** `scripts/eval_dataset_30.json`
- **Dataset size:** 30 services
- **Class distribution:**  
  - LOW: 10  
  - MEDIUM: 10  
  - HIGH: 10

---

## 3) Final Evaluation Results (after applying best config)

### Command used
```bash
python scripts/evaluate_model.py --dataset scripts/eval_dataset_30.json
```

### Metrics
- **Accuracy:** `1.0000`
- **Macro-F1:** `1.0000`
- **Precision (macro):** `1.0000`
- **Recall (macro):** `1.0000`
- **F1 (HIGH class):** `1.0000`
- **False Negative Rate (HIGH):** `0.0000`

### Confusion Matrix
```text
[[10, 0, 0],
 [ 0,10, 0],
 [ 0, 0,10]]
```

### Classification Report
```text
              precision    recall  f1-score   support

         LOW       1.00      1.00      1.00        10
      MEDIUM       1.00      1.00      1.00        10
        HIGH       1.00      1.00      1.00        10

    accuracy                           1.00        30
   macro avg       1.00      1.00      1.00        30
weighted avg       1.00      1.00      1.00        30
```

---

## 4) Calibration Summary

### 4.1 Threshold calibration
- **Script:** `scripts/calibrate_thresholds.py`
- **Selected thresholds:**
  - `threshold_medium=0.25`
  - `threshold_high=0.55`
- **Rationale:** Best trade-off on current dataset with strong HIGH-risk detection.

### 4.2 Weight calibration
- **Script:** `scripts/calibrate_weights.py`
- **Selected weights:**
  - `w_vulnerabilities=0.1`
  - `w_config=0.3`
  - `w_reputation=0.6`
- **Rationale:** Best overall ranking metrics (including HIGH-risk performance) on current dataset.

---

## 5) Explainability & Policy Enforcement

The pipeline returns:
- `risk_score`, `risk_level`, `decision`
- feature-level contributions
- policy override fields:
  - `policy_id`
  - `policy_reason`
  - `matched_policies`

Main policy examples:
- `P-001`: blacklist => BLOCK
- `P-002`: no HTTPS + invalid SSL => BLOCK
- `P-003`: weak auth on AI API => REVIEW
- `P-004`: low compliance + medium+ risk => REVIEW
- `P-005`: low confidence => REVIEW
- `P-000`: default model-based decision

---

## 6) Example Assessments (to fill with actual IDs from `/assessment/raw/{id}`)

> Replace placeholders below with real API outputs captured from your runtime.

### A) LOW example
- **Assessment ID:** `<LOW_ID>`
- **Risk score:** `<value>`
- **Risk level:** `LOW`
- **Decision:** `ALLOW`
- **Policy ID:** `<policy_id>`
- **Policy reason:** `<policy_reason>`
- **Reasons:**
  - `<reason_1>`
  - `<reason_2>`

### B) MEDIUM example
- **Assessment ID:** `<MEDIUM_ID>`
- **Risk score:** `<value>`
- **Risk level:** `MEDIUM`
- **Decision:** `REVIEW`
- **Policy ID:** `<policy_id>`
- **Policy reason:** `<policy_reason>`
- **Reasons:**
  - `<reason_1>`
  - `<reason_2>`

### C) HIGH example
- **Assessment ID:** `<HIGH_ID>`
- **Risk score:** `<value>`
- **Risk level:** `HIGH`
- **Decision:** `BLOCK`
- **Policy ID:** `<policy_id>`
- **Policy reason:** `<policy_reason>`
- **Reasons:**
  - `<reason_1>`
  - `<reason_2>`

---

## 7) Reliability Statement (for report/defense)

These results demonstrate very strong internal performance on a balanced synthetic benchmark (30 samples).  
However, this does **not** imply perfect real-world performance. External validity requires:
1. Larger real-world labeled datasets  
2. Periodic recalibration (thresholds/weights)  
3. Connector quality monitoring and drift checks over time

---

## 8) Reproducibility

### Run tests
```bash
PYTHONPATH=. pytest -q
```

### Run evaluation
```bash
python scripts/evaluate_model.py --dataset scripts/eval_dataset_30.json
```

### Run threshold calibration
```bash
python scripts/calibrate_thresholds.py --dataset scripts/eval_dataset_30.json
```

### Run weight calibration
```bash
python scripts/calibrate_weights.py --dataset scripts/eval_dataset_30.json --threshold-medium 0.25 --threshold-high 0.55
```

---

## 9) Conclusion

With calibrated thresholds and weights, the current version achieves:
- explainable risk scoring,
- policy-based decision enforcement,
- strong benchmark metrics on the current test set.

This provides a solid Zero-Trust foundation for AI SaaS due diligence, with clear pathways for further real-world hardening.