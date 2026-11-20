# Task: slugify

Add `slugify(title)` to `text_utils.py`.

Acceptance checks:
- Lowercases everything
- Spaces become hyphens
- Anything that is not a-z, 0-9 or a hyphen is removed
- Repeated hyphens collapse to one, and there is no hyphen at either end
- `slugify("  Hello,  World!! ")` returns `"hello-world"`
