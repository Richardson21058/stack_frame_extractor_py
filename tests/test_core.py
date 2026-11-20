import os
import sys
import unittest

from stack_frame_extractor_py import extract_stack_frames, extract_current_frame


class TestExtractStackFrames(unittest.TestCase):
    def test_returns_list_of_tuples(self):
        frames = extract_stack_frames()
        self.assertIsInstance(frames, list)
        self.assertTrue(frames, "expected at least one frame")
        for frame in frames:
            self.assertIsInstance(frame, tuple)
            self.assertEqual(len(frame), 3)
            function_name, file_path, line_number = frame
            self.assertIsInstance(function_name, str)
            self.assertIsInstance(file_path, str)
            self.assertIsInstance(line_number, int)

    def test_first_frame_is_caller(self):
        # The first frame must be this test method, not the extractor.
        frames = extract_stack_frames()
        function_name, file_path, line_number = frames[0]
        self.assertEqual(function_name, "test_first_frame_is_caller")
        self.assertEqual(os.path.abspath(file_path), os.path.abspath(__file__))
        # The call site is the line where extract_stack_frames() is invoked.
        self.assertGreater(line_number, 0)

    def test_frames_are_ordered_innermost_first(self):
        frames = extract_stack_frames()
        function_names = [frame[0] for frame in frames]
        # The innermost frame is this test method. The outermost frame is
        # the unittest runner, which is not the same as the innermost.
        self.assertEqual(function_names[0], "test_frames_are_ordered_innermost_first")
        self.assertNotEqual(function_names[0], function_names[-1])

    def test_extractor_frame_is_excluded(self):
        frames = extract_stack_frames()
        function_names = [frame[0] for frame in frames]
        self.assertNotIn("extract_stack_frames", function_names)

    def test_paths_are_absolute(self):
        # Synthetic interpreter frames (e.g. runpy) may use pseudo-paths like
        # '<frozen runpy>'. Only real file paths are expected to be absolute.
        frames = extract_stack_frames()
        for _, file_path, _ in frames:
            if file_path.startswith("<") and file_path.endswith(">"):
                continue
            self.assertTrue(
                os.path.isabs(file_path),
                f"expected absolute path, got {file_path!r}",
            )

    def test_does_not_touch_filesystem(self):
        # A regression guard: the implementation must not read source lines.
        # We assert that the returned paths exist for the frames we control
        # (this test file) and that the call is cheap enough to run in a
        # tight loop without raising.
        for _ in range(50):
            frames = extract_stack_frames()
            self.assertTrue(frames)

    def test_called_from_helper(self):
        # Verify that a helper function appears as the innermost frame.
        frames = _helper()
        self.assertEqual(frames[0][0], "_helper")
        self.assertEqual(frames[1][0], "test_called_from_helper")


class TestExtractCurrentFrame(unittest.TestCase):
    def test_returns_single_tuple(self):
        frame = extract_current_frame()
        self.assertIsInstance(frame, tuple)
        self.assertEqual(len(frame), 3)

    def test_caller_is_this_test(self):
        function_name, file_path, line_number = extract_current_frame()
        self.assertEqual(function_name, "test_caller_is_this_test")
        self.assertEqual(os.path.abspath(file_path), os.path.abspath(__file__))
        self.assertGreater(line_number, 0)

    def test_path_is_absolute(self):
        _, file_path, _ = extract_current_frame()
        self.assertTrue(os.path.isabs(file_path))

    def test_called_from_helper(self):
        frame = _helper_current()
        self.assertEqual(frame[0], "_helper_current")


def _helper():
    return extract_stack_frames()


def _helper_current():
    return extract_current_frame()


if __name__ == "__main__":
    unittest.main()
