## infrastructure/classifier

Sensitivity classification for documents.

### Files

`sensitivity_model.py` - receives extracted text and returns a SensitivityLevel. Can be rule-based (keyword matching) or an ML model. The result is used by the IngestJob to decide whether to trigger a human review.
