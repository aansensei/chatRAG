## application/review

Use cases for the human review workflow. Applies to documents with SensitivityLevel >= CONFIDENTIAL.

### Files

`get_pending.py` - returns a list of Reviews in PENDING state, used for the reviewer dashboard.

`approve_review.py` - reviewer approves a document: updates Review to APPROVED, transitions Document to READY, publishes `ReviewApproved` event.

`reject_review.py` - reviewer rejects a document: updates Review to REJECTED, document is not deployed to the search index.
