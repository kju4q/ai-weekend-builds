# Task: fetch every page

`fetch_all(client)` must return every item from an API that pages results.
Each response is `{"items": [...], "next": cursor or None}`.

Acceptance checks:
- Returns the items from every page, including the last one
- Stops when `next` is None
- Works when there is only one page
