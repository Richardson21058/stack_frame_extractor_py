"""Core implementation for capturing call stack frames.

Design notes
------------

The extractor is deliberately built on the standard library's ``inspect``
module rather than ``sys._getframe``. ``inspect.stack`` is documented, stable
across CPython versions, and already filters out the extractor's own internal
frames when called through ``context``. That matters because callers want the
frames of *their* code, not the frames of the helper they called.

Two public functions are exported:

``extract_stack_frames``
    Returns a list of ``(function_name, file_path, line_number)`` tuples for
the current call stack, starting with the caller of this function and ending
with the outermost frame.

``extract_current_frame``
    Returns a single ``(function_name, file_path, line_number)`` tuple for the
frame that called this function. It is a convenience wrapper for the common
case where only one frame of context is needed.

A deliberate trade-off: the returned file paths are absolute. Relative paths
are cheaper to print, but they become meaningless as soon as the error context
is logged from a different working directory. Absolute paths are portable
enough for log aggregation and are what most error-reporting backends expect.
"""

from __future__ import annotations

import inspect
from typing import List, Tuple

FrameTuple = Tuple[str, str, int]


def extract_stack_frames() -> List[FrameTuple]:
    """Capture the current call stack as a list of frame tuples.

    The list is ordered from the innermost frame (the caller of this
    function) to the outermost frame. Each tuple is
    ``(function_name, file_path, line_number)``.

    The extractor's own frame is excluded so that callers see only their
    own code. ``inspect.stack`` is used with ``context=0`` to avoid reading
    source lines, which keeps the function cheap and avoids touching the
    filesystem.

    Returns:
        A list of ``(function_name, file_path, line_number)`` tuples. The
        list is empty only if the interpreter reports no frames, which is
        not expected in normal operation but is handled defensively.
    """
    frames = inspect.stack(context=0)

    # inspect.stack()[0] is this function's own frame. Drop it so the first
    # entry the caller sees is the code that called us.
    caller_frames = frames[1:]

    result: List[FrameTuple] = []
    for frame_info in caller_frames:
        function_name = frame_info.function
        file_path = frame_info.filename
        line_number = frame_info.lineno
        result.append((function_name, file_path, line_number))
    return result


def extract_current_frame() -> FrameTuple:
    """Capture a single frame tuple for the immediate caller.

    This is a convenience wrapper around ``extract_stack_frames`` for the
    common case where only one frame is needed. It avoids allocating a list
    of every frame on the stack.

    Returns:
        A ``(function_name, file_path, line_number)`` tuple describing the
        frame that called this function.

    Raises:
        RuntimeError: If the interpreter reports no caller frame. This is
            not expected in normal operation but is raised rather than
            returning a sentinel so that a broken stack is loud.
    """
    frames = inspect.stack(context=0)

    # frames[0] is this function, frames[1] is the caller. If the stack is
    # somehow truncated, raise rather than fabricate a frame.
    if len(frames) < 2:
        raise RuntimeError("no caller frame available")

    frame_info = frames[1]
    return (frame_info.function, frame_info.filename, frame_info.lineno)
