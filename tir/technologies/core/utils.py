from tir.technologies.core.logging_config import logger
from selenium.common.exceptions import TimeoutException
from typing import Iterable, Optional, Set
import inspect
import time
import os

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
    
    def driver_get(self, inst, url: str) -> bool:
        """Navigate the browser to the given URL with retry logic.

        Attempts to load the URL repeatedly until success or timeout.
        On ``TimeoutException`` the request is retried; any other exception
        aborts immediately and logs the error.

        Args:
            inst: Test instance containing ``driver``, ``config`` and ``log_error``.
            url: The URL to navigate to.

        Returns:
            bool: ``True`` if the page loaded successfully, ``False`` otherwise.
        """
        endtime = time.time() + inst.config.time_out
        success = False

        inst.driver.set_page_load_timeout(120)

        while time.time() < endtime and not success:
            try:
                inst.driver.get(url)
                success = True
            except TimeoutException:
                logger().info(f"Timeout while loading '{url}'. Retrying...")
            except Exception as e:
                logger().error(f"Unexpected error while loading '{url}': {e}")
                success = False
                break

        if not success:
            inst.log_error(f"Failed to load page '{url}' within {inst.config.time_out}s timeout.")

        return success
