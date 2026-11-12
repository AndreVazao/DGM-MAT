# Browser consultation result retrieval

## Why

The browser consultation queue already stores completed provider responses and
the mission-linking API records their SHA-256 receipts. The operator control
surface lacked a dedicated read endpoint for retrieving the final response by
consultation ID. Queue approval therefore did not provide a complete
operator-facing read-back contract.

## Endpoint

`GET /recovery/browser-consult/result/{consultation_id}`

The endpoint requires an authenticated local DGM-MAT principal with the
`browser-consult-control` scope. It returns the consultation's task reference,
provider, lifecycle status, timestamps, bounded stored response, response
SHA-256, error classification and review identifiers.

It never returns the extension claim token or the queued prompt. Responses are
explicitly marked `result_trusted=false`, `independence_attested=false` and
`accepted=null`. A provider response is evidence for human review, not an
approved action or proof of correctness.

## Validation

Focused API tests cover successful completion/read-back, missing and malformed
IDs, token/prompt non-disclosure, untrusted-result flags and route-scope
classification. The paired extension retains its narrower capture scopes and
does not gain access to this operator endpoint.
