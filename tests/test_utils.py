"""Unit tests for Utils class and its methods."""

import inspect
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add the parent directory to the path so we can import tir module
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from tir.technologies.core.utils import Utils


class TestUtilsGetMainEntrypointFromStack(unittest.TestCase):
    """Test cases for Utils.get_main_entrypoint_from_stack method."""

    def setUp(self):
        """Initialize test fixtures."""
        self.utils = Utils()

    def test_get_main_entrypoint_with_default_parameters(self):
        """Test method returns a string value with default parameters."""
        result = self.utils.get_main_entrypoint_from_stack()
        self.assertIsInstance(result, str)

    def test_get_main_entrypoint_returns_fallback_when_no_match(self):
        """Test method returns fallback value when no matching frame is found."""
        result = self.utils.get_main_entrypoint_from_stack(
            target_modules=["nonexistent/module.py"],
            fallback="custom_fallback"
        )
        self.assertEqual(result, "custom_fallback")

    def test_get_main_entrypoint_returns_default_fallback(self):
        """Test method returns default fallback when no matching frame is found."""
        result = self.utils.get_main_entrypoint_from_stack(
            target_modules=["nonexistent/module.py"]
        )
        self.assertEqual(result, "function_name")

    def test_get_main_entrypoint_ignores_specified_functions(self):
        """Test that specified functions in ignored_functions are skipped."""
        # Create a set of functions to ignore
        ignored_set = {"__getattribute__", "_subscribe_routes", "__init__", "<lambda>"}
        
        result = self.utils.get_main_entrypoint_from_stack(
            target_modules=["test_utils.py"],
            ignored_functions=ignored_set,
            fallback="test_fallback"
        )
        
        # The result should not be in the ignored set or should be fallback
        if result != "test_fallback":
            self.assertNotIn(result, ignored_set)

    def test_get_main_entrypoint_with_custom_ignored_functions(self):
        """Test method with custom ignored functions set."""
        custom_ignored = {"test_method", "setup"}
        result = self.utils.get_main_entrypoint_from_stack(
            target_modules=["test_utils.py"],
            ignored_functions=custom_ignored,
            fallback="not_found"
        )
        
        self.assertIsInstance(result, str)

    def test_get_main_entrypoint_case_insensitive_matching(self):
        """Test that module matching is case-insensitive."""
        # Test with uppercase module name
        result1 = self.utils.get_main_entrypoint_from_stack(
            target_modules=["TEST_UTILS.PY"],
            fallback="not_found"
        )
        
        # Test with lowercase module name
        result2 = self.utils.get_main_entrypoint_from_stack(
            target_modules=["test_utils.py"],
            fallback="not_found"
        )
        
        # Both should return the same result
        self.assertEqual(result1, result2)

    def test_get_main_entrypoint_with_path_separators(self):
        """Test that method handles both forward and backward slashes."""
        # Test with forward slashes
        result1 = self.utils.get_main_entrypoint_from_stack(
            target_modules=["tests/test_utils.py"],
            fallback="not_found"
        )
        
        # Test with backward slashes (Windows style)
        result2 = self.utils.get_main_entrypoint_from_stack(
            target_modules=["tests\\test_utils.py"],
            fallback="not_found"
        )
        
        # Both should return the same result
        self.assertEqual(result1, result2)

    def test_get_main_entrypoint_multiple_target_modules(self):
        """Test method with multiple target modules."""
        result = self.utils.get_main_entrypoint_from_stack(
            target_modules=["nonexistent.py", "test_utils.py", "another.py"],
            fallback="not_found"
        )
        
        self.assertIsInstance(result, str)

    @patch('inspect.stack')
    def test_get_main_entrypoint_with_mocked_stack(self, mock_stack):
        """Test method behavior with mocked call stack."""
        # Create mock stack frames
        mock_frame1 = MagicMock()
        mock_frame1.filename = "c:\\TOTVS\\repos\\tir\\tir\\main.py"
        mock_frame1.function = "test_function"
        
        mock_frame2 = MagicMock()
        mock_frame2.filename = "c:\\other\\path\\module.py"
        mock_frame2.function = "other_function"
        
        mock_stack.return_value = [mock_frame1, mock_frame2]
        
        result = self.utils.get_main_entrypoint_from_stack(
            target_modules=["tir/main.py"]
        )
        
        self.assertEqual(result, "test_function")

    @patch('inspect.stack')
    def test_get_main_entrypoint_skips_ignored_functions(self, mock_stack):
        """Test that method skips frames with ignored functions."""
        # Create mock stack frames
        mock_frame1 = MagicMock()
        mock_frame1.filename = "c:\\TOTVS\\repos\\tir\\tir\\main.py"
        mock_frame1.function = "__init__"  # This should be ignored
        
        mock_frame2 = MagicMock()
        mock_frame2.filename = "c:\\TOTVS\\repos\\tir\\tir\\main.py"
        mock_frame2.function = "user_function"  # This should be returned
        
        mock_stack.return_value = [mock_frame1, mock_frame2]
        
        result = self.utils.get_main_entrypoint_from_stack(
            target_modules=["tir/main.py"]
        )
        
        self.assertEqual(result, "user_function")

    @patch('inspect.stack')
    def test_get_main_entrypoint_returns_first_match(self, mock_stack):
        """Test that method returns the first matching function."""
        # Create mock stack frames
        mock_frame1 = MagicMock()
        mock_frame1.filename = "c:\\TOTVS\\repos\\tir\\tir\\main.py"
        mock_frame1.function = "first_function"
        
        mock_frame2 = MagicMock()
        mock_frame2.filename = "c:\\TOTVS\\repos\\tir\\tir\\main.py"
        mock_frame2.function = "second_function"
        
        mock_stack.return_value = [mock_frame1, mock_frame2]
        
        result = self.utils.get_main_entrypoint_from_stack(
            target_modules=["tir/main.py"]
        )
        
        # Should return the first matching function
        self.assertEqual(result, "first_function")

    def test_get_main_entrypoint_empty_ignored_functions(self):
        """Test method with empty ignored functions set."""
        result = self.utils.get_main_entrypoint_from_stack(
            target_modules=["test_utils.py"],
            ignored_functions=set(),
            fallback="fallback"
        )
        
        self.assertIsInstance(result, str)

    def test_get_main_entrypoint_returns_string_type(self):
        """Test that method always returns a string."""
        test_cases = [
            {"target_modules": None},
            {"target_modules": ["nonexistent.py"]},
            {"fallback": "custom"},
            {"ignored_functions": set()},
        ]
        
        for kwargs in test_cases:
            result = self.utils.get_main_entrypoint_from_stack(**kwargs)
            self.assertIsInstance(result, str, 
                                f"Expected str, got {type(result)} for kwargs: {kwargs}")

    def test_utils_instantiation(self):
        """Test that Utils class can be instantiated."""
        utils_instance = Utils()
        self.assertIsNotNone(utils_instance)
        self.assertTrue(hasattr(utils_instance, 'get_main_entrypoint_from_stack'))

    def test_get_main_entrypoint_with_absolute_path_module(self):
        """Test method with absolute path in target_modules."""
        abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_utils.py"))
        
        result = self.utils.get_main_entrypoint_from_stack(
            target_modules=[abs_path],
            fallback="not_found"
        )
        
        self.assertIsInstance(result, str)


class TestUtilsClass(unittest.TestCase):
    """Test cases for Utils class itself."""

    def test_utils_has_get_main_entrypoint_method(self):
        """Test that Utils class has the get_main_entrypoint_from_stack method."""
        utils = Utils()
        self.assertTrue(hasattr(utils, 'get_main_entrypoint_from_stack'))
        self.assertTrue(callable(getattr(utils, 'get_main_entrypoint_from_stack')))

    def test_utils_docstring_exists(self):
        """Test that Utils class has proper documentation."""
        self.assertIsNotNone(Utils.__doc__)
        self.assertTrue(len(Utils.__doc__) > 0)

    def test_get_main_entrypoint_docstring_exists(self):
        """Test that method has proper documentation."""
        method = Utils.get_main_entrypoint_from_stack
        self.assertIsNotNone(method.__doc__)
        self.assertTrue(len(method.__doc__) > 0)


if __name__ == '__main__':
    unittest.main()
