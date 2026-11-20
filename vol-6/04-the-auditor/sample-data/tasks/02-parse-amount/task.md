# Task: parse amounts from bank CSVs

Add `parse_amount(s)` to `money.py`.

Acceptance checks:
- `"1,234.50"` returns `1234.5`
- `"-12.00"` returns `-12.0`
- `"(12.00)"` returns `-12.0` (some banks write negatives in parentheses)
- Empty string raises `ValueError`
