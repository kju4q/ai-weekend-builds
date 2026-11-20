# Task: never DM the same comment twice

The webhook can deliver the same comment event more than once, including after
the server restarts. Make sure each comment id gets at most one DM.

Acceptance checks:
- The same comment id delivered twice sends one DM
- This still holds after the server process restarts
- Every send is recorded in the `sends` table
