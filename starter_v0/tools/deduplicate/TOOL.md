---
name: deduplicate
track: core
kind: local_formatter
provider: none
requires_env: []
inputs: [items]
outputs: [items, input_count, item_count, removed_count]
side_effect: false
requires_confirmation: false
---

# deduplicate

Remove duplicate items by URL from an existing list.

Use when the user requests duplicate removal before creating a digest.
This tool does not search the web or fetch content.

## Behavior

- Compare URLs exactly after trimming surrounding whitespace.
- Keep the first item for each URL and preserve input order.
- Keep items without a usable URL.
- Return an error dictionary for invalid input.
- Different URLs with similar content are not considered duplicates.