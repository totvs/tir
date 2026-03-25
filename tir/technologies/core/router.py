
from tir.technologies.core.config import ConfigLoader
from tir.technologies.core.language import LanguagePack

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
        self.language = LanguagePack(self.config.language) if self.config.language else ""

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

    def Program(self, program_name: str = "", program_desc: str = "") -> None:
        """Execute program using appropriate driver (POUI or WebApp)."""

        drv = self._get_driver_instance(lambda: self.config.new_home)
        drv.Program(program_name=program_name, program_desc=program_desc)

        """
        Sync POUI → WebApp program name (new_home):
        WebApp and POUI use separate Log instances. If the test filename is misspelled 
        (e.g., TESTECASE.py), get_program_name() fails and Program() sets self.log.program 
        only on POUI. Copying it here ensures WebApp's generate_log() uses the correct 
        program.
        """
        if self.config.new_home and not self._ensure_webapp().log.program:
            self._ensure_webapp().log.program = self._ensure_poui().log.program

    def set_program(self, program_name: str = "", program_desc: str = "") -> None:
        """Set program using appropriate driver (POUI or WebApp)."""

        drv = self._get_driver_instance(lambda: self.config.new_home)
        drv.set_program(program_name=program_name, program_desc=program_desc)

    def SetLateralMenu(self, menu_itens: str, save_input: bool = True, click_menu_functional: bool = False) -> None:
        """Navigate through lateral menu."""

        drv = self._get_driver_instance(lambda: self.config.new_home)
        drv.SetLateralMenu(menu_itens=menu_itens, save_input=save_input, click_menu_functional=click_menu_functional)

    def ChangeEnvironment(self, date: str = "", group: str = "", branch: str = "", module: str = "") -> None:
        """Change environment settings."""

        drv = self._get_driver_instance(lambda: self.config.new_home)
        drv.ChangeEnvironment(date=date, group=group, branch=branch, module=module)

    def Finish(self) -> None:
        """Finish using appropriate driver (POUI or WebApp)."""

        drv = self._get_driver_instance(lambda: self.config.new_home)
        drv.Finish()

    def set_log_info(self) -> None:
        """Set Log Info using appropriate driver (POUI or WebApp)."""

        drv = self._get_driver_instance(lambda: self.config.new_home)
        drv.set_log_info()

    def SetButton(self, button, sub_item="", position=1, check_error=True) -> None:
        """Click on button using appropriate driver (POUI or WebApp)."""

        view          = self.language.view
        change        = self.language.old_browse_edit
        other_actions = self.language.other_actions
        delete        = self.language.old_browse_delete
        add           = self.language.old_browse_insert

        new_browse_buttons = [view, change, other_actions, delete, add]

        new_browse = self._ensure_poui().check_new_search_browse()
        drv = self._get_driver_instance(lambda: new_browse and button in new_browse_buttons)
        drv.SetButton(button, sub_item, position, check_error=check_error)


        