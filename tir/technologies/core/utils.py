import inspect
import os
from typing import Iterable, Optional, Set


class Utils:
    """Shared utility methods for TIR technologies."""

    def get_main_entrypoint_from_stack(
        self,
        target_modules: Optional[Iterable[str]] = None,
        ignored_functions: Optional[Set[str]] = None,
        fallback: str = "function_name"
    ) -> str:
        """Return the external entrypoint function from call stack.

        Retrieves the name of the first function in the call stack that matches the target
        modules and is not in the ignored functions set. Useful for identifying which test
        method or user function initiated a chain of internal calls.

        Args:
            target_modules: Iterable of module paths to search for (e.g., "tir/main.py").
                          Default: ("tir/main.py",). Must be relative or absolute paths.
            ignored_functions: Set of function names to exclude from results 
                             (e.g., "__init__", "<lambda>"). 
                             Default: {"__getattribute__", "_subscribe_routes", "__init__", "<lambda>"}
            fallback: Value to return if no matching frame is found. Default: "function_name"

        Returns:
            str: The name of the matching function, or fallback value if no match found.

        Examples:
            >>> utils = Utils()
            >>> # Get entrypoint with defaults
            >>> utils.get_main_entrypoint_from_stack()
            'my_test_method'
            
            >>> # Get entrypoint from custom module
            >>> utils.get_main_entrypoint_from_stack(target_modules=["custom/module.py"])
            'custom_function'
            
            >>> # Custom ignored functions
            >>> utils.get_main_entrypoint_from_stack(
            ...     ignored_functions={"__init__", "setup"}
            ... )
            'test_something'
        """
        modules = tuple(target_modules) if target_modules else ("tir/main.py",)
        ignored = ignored_functions or {"__getattribute__", "_subscribe_routes", "__init__", "<lambda>"}

        # Normalize all target modules to lowercase with forward slashes
        normalized_modules = tuple(
            os.path.normpath(module).replace("\\", "/").lower()
            for module in modules
        )

        # Iterate through call stack frames
        for stack_item in inspect.stack():
            # Normalize the frame's filename for comparison
            filename = os.path.normpath(stack_item.filename).replace("\\", "/").lower()
            
            # Check if filename matches any target module (case-insensitive, path-aware)
            # Use path matching to avoid false positives (e.g., avoiding "my_main.py" matching "main.py")
            matches_target = any(
                filename.endswith(os.path.sep.replace("\\", "/") + module) or 
                filename.endswith("/" + module) or
                filename == module
                for module in normalized_modules
            )
            
            # Return the function name if it matches and is not ignored
            if matches_target and stack_item.function not in ignored:
                return stack_item.function

        return fallback
