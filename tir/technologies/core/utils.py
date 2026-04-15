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

        Looks for the first stack frame whose filename ends with one of target modules
        and whose function is not in ignored_functions.
        """
        modules = tuple(target_modules) if target_modules else ("tir/main.py",)
        ignored = ignored_functions or {"__getattribute__", "_subscribe_routes", "__init__", "<lambda>"}

        normalized_modules = tuple(
            os.path.normpath(module).replace("\\", "/").lower()
            for module in modules
        )

        for stack_item in inspect.stack():
            filename = os.path.normpath(stack_item.filename).replace("\\", "/").lower()
            if any(filename.endswith(module) for module in normalized_modules) and stack_item.function not in ignored:
                return stack_item.function

        return fallback
