# Task: retry on rate limits

Wrap `send(request)` so that a 429 response is retried up to 3 times with
exponential backoff (1s, 2s, 4s).

Acceptance checks:
- A 429 is retried, at most 3 times
- Any other error status is raised immediately, not retried
- A success returns the response
