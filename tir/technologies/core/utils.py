from typing import Iterable, Optional, Set
import inspect
import os
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from tir.technologies.core.logging_config import logger
import tir.technologies.core.enumerations as enum

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

    def check_tmenu_screen(self, caller) -> bool:
        """[Internal]
        
        Checks if the main menu screen (tmenu) is currently displayed.
        
        Args:
            caller: The technology instance with config, web_scrap, and element_is_displayed methods.
        
        Returns:
            bool: True if menu screen is displayed, False otherwise.
        """
        
        
        try:
            twebview = True if caller.config.new_home else False
            return caller.element_is_displayed(
                next(iter(caller.web_scrap(term=".tmenu, .dict-tmenu, [class*='card-wrapper']", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body", twebview=twebview)),
                     None))
        except:
            return False

    def escape_to_main_menu(
        self,
        caller,
        container_term: Optional[str] = None
    ) -> None:
        """Navigate back to the main menu by sending ESC keys and closing open dialogs.

        Waits until the main menu screen is visible and, when `container_term` is provided,
        verifies that only one dialog layer remains before declaring success.

        Args:
            caller: The technology instance (WebappInternal or PouiInternal) that owns
                    the driver, config, and helper methods.
            container_term: CSS selector used to count dialog layers and confirm only
                            one remains before declaring success.
                        Default: None (no layer check). Webapp should pass
                        "wa-dialog".
        """
        
        success = False

        endtime = time.time() + caller.config.time_out / 2
        while time.time() < endtime and not success:
            logger().info('Escape to menu')
            ActionChains(caller.driver).send_keys(Keys.ESCAPE).perform()

            if any([caller.check_warning_screen(), caller.check_coin_screen(), caller.check_news_screen()]) \
                    and (not container_term or caller.check_layers(container_term) > 1):
                logger().info('Found layers after Escape to menu')
                caller.close_screen_before_menu()

            menu_screen = self.check_tmenu_screen(caller)
            container_layers = (caller.check_layers(container_term) == 1) if container_term else True
            success = menu_screen and container_layers

            logger().debug(f'Check Menu Screen: {menu_screen}')
            if container_term:
                logger().debug(f'{container_term} layers: {container_layers}')

        if not success:
            caller.log_error('Home screen not found!')
