# stack_frame_extractor_py

Captures the current call stack and returns a list of
`(function_name, file_path, line_number)` tuples for attaching to error
context.

```python
from stack_frame_extractor_py import extract_stack_frames, extract_current_frame


def risky_operation():
    frames = extract_stack_frames()
    for function_name, file_path, line_number in frames:
        print(f"{function_name} at {file_path}:{line_number}")

    # If you only need one frame, use the convenience wrapper.
    function_name, file_path, line_number = extract_current_frame()
    print(f"called from {function_name} at {file_path}:{line_number}")
```

## Why this exists

When an exception is caught and logged, the traceback is usually enough. But
some systems — structured loggers, error-reporting backends, background
workers — want the call stack as data, not as a formatted string. The standard
library gives you `traceback.extract_stack()` and `inspect.stack()`, but both
return rich objects that carry more than most callers need and are awkward to
serialize.

This library wraps `inspect.stack()` and flattens each frame to a plain tuple
of the three fields that matter for error context: the function name, the
absolute file path, and the line number. The trade-off is that you lose
access to the frame object itself and to the source line text. If you need
those, use `inspect.stack()` directly. The benefit is a small, dependency-free
value that drops straight into JSON, log records, or a tuple column in a
database.

The extractor's own frame is excluded, so the first tuple describes the code
that called `extract_stack_frames()`, not the library internals.

## The awkward edge

File paths are absolute. If you were expecting paths relative to the current
working directory, you will be surprised: a relative path is meaningless once
the error context is shipped to a log aggregator that runs from a different
directory. Absolute paths are the portable choice for that use case. If you
need relative paths, strip the prefix yourself at the point where you know
what the project root is.

## Exported names

- `extract_stack_frames()` — returns a `list` of `(function_name, file_path,
  line_number)` tuples, ordered innermost first, excluding the extractor's own
  frame.
- `extract_current_frame()` — returns a single `(function_name, file_path,
  line_number)` tuple for the immediate caller.

## Running the tests

```sh
PYTHONPATH=src python -m unittest discover -s tests
```
