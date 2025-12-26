
from tir.technologies.core.config import ConfigLoader
import time

class Router:
    """
    Routes method calls between POUI and WebApp implementations dynamically.

    This class maintains backward compatibility with existing test scripts while
    enabling transparent migration from WebApp to POUI. It automatically selects
    the appropriate driver based on runtime configuration.

    Design Patterns:
    - **Strategy**: Selects POUI or WebApp at runtime based on configuration
      (e.g., `config.new_home` flag). Needed because Protheus is gradually
      migrating screens from WebApp to POUI.

    - **Adapter**: Translates method calls when interfaces differ between.

    :param config_path: Path to config.json file
    :param inst_webapp: Optional WebappInternal instance for injection
    :param inst_poui: Optional PouiInternal instance for injection

    Note: Driver instances are created lazily only when needed.
    """

    def __init__(self, config_path="", inst_webapp=None, inst_poui=None):
        self.config = ConfigLoader()
        self._config_path = config_path
        self.__webapp = None
        self.__poui = None
        inst_webapp and self.set_webapp(inst_webapp)
        inst_poui and self.set_poui(inst_poui)

    def set_webapp(self, inst):
        """Setter for WebappInternal instance."""
        self.__webapp = inst

    def set_poui(self, inst):
        """Setter for PouiInternal instance."""
        self.__poui = inst

    def _ensure_webapp(self):
        """Get or lazily create WebappInternal instance.
        
        Recreates the instance if driver is closed or None.
        """
        if self.__webapp is None or not self._is_driver_active(self.__webapp):
            from tir.technologies.webapp_internal import WebappInternal
            self.__webapp = WebappInternal(self._config_path, autostart=False)
        
        return self.__webapp

    def _ensure_poui(self):
        """Get or lazily create PouiInternal instance.
        
        Recreates the instance if driver is closed or None.
        """
        if self.__poui is None or not self._is_driver_active(self.__poui):
            from tir.technologies.poui_internal import PouiInternal
            self.__poui = PouiInternal(self._config_path, autostart=False)
        
        return self.__poui
    
    def _is_driver_active(self, instance):
        """Check if instance has an active driver."""
        try:
            if not hasattr(instance, 'driver') or instance.driver is None:
                return False
            # Try accessing current_url to verify if session is active
            _ = instance.driver.current_url
            return True
        except Exception:
            return False
    
    def _get_driver_instance(self, condition_fn):
        """Get driver instance based on condition.
        
        Returns PouiInternal if condition is True, otherwise WebappInternal.
        """
        return self._ensure_poui() if condition_fn() else self._ensure_webapp()

    def Program(self, program_name: str) -> None:
        """Execute program using appropriate driver (POUI or WebApp)."""
        drv = self._get_driver_instance(lambda: self.config.new_home)
        drv.Program(program_name)

        if self.config.new_home:
            # Should close all 3 only for SIGAADV, but on new home they appear regardless of initial program
            self._ensure_webapp().close_warning_screen_after_routine()
            if self.config.initial_program.lower() == 'sigaadv':
                self._ensure_webapp().close_coin_screen_after_routine()
                self._ensure_webapp().close_news_screen_after_routine()

            if (self.config.initial_program.lower() == 'sigaloja' or \
                program_name.lower().startswith('loj') or \
                program_name.lower().startswith('ljl')):
                time.sleep(2)
                self._ensure_webapp().close_modal()

    def set_program(self, program_name: str) -> None:
        """Set program using appropriate driver (POUI or WebApp)."""
        drv = self._get_driver_instance(lambda: self.config.new_home)
        drv.set_program(program_name)

        if self.config.new_home:
            # Should close all 3 only for SIGAADV, but on new home they appear regardless of initial program
            self._ensure_webapp().close_warning_screen_after_routine()
            if self.config.initial_program.lower() == 'sigaadv':
                self._ensure_webapp().close_coin_screen_after_routine()
                self._ensure_webapp().close_news_screen_after_routine()

            if (self.config.initial_program.lower() == 'sigaloja' or \
                program_name.lower().startswith('loj') or \
                program_name.lower().startswith('ljl')):
                time.sleep(2)
                self._ensure_webapp().close_modal()

    def SetLateralMenu(self, menu_itens: str, save_input: bool = True, click_menu_functional: bool = False) -> None:
        """Navigate through lateral menu.
        
        Note: Not yet implemented for new home page.
        """

        if self.config.new_home:
            self._ensure_webapp().config.routine = None
            self._ensure_webapp().config.routine_type = None
            self._ensure_webapp().log_error('The SetLateralMenu function has not yet been implemented on the new home page.')
        else:            
            self._ensure_webapp().SetLateralMenu(menu_itens, save_input, click_menu_functional)

    def ChangeEnvironment(self, date: str = "", group: str = "", branch: str = "", module: str = "") -> None:
        """Change environment settings.
        
        Note: Not yet implemented for new home page.
        """

        if self.config.new_home:
            self.config.date = date if date else self.config.date
            self.config.group = group if group else self.config.group
            self.config.branch = branch if branch else self.config.branch
            self.config.module = module if module else self.config.module

            self._ensure_webapp().get_url(self.config.url)
            self._ensure_webapp().Setup(
                initial_program=self.config.initial_program,
                date=self.config.date,
                group=self.config.group,
                branch=self.config.branch,
                module=self.config.module
            )
        else:            
            self._ensure_webapp().ChangeEnvironment(date, group, branch, module)