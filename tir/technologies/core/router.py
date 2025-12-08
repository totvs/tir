
from tir.technologies.core.config import ConfigLoader

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

    - **Adapter**: Translates method calls when interfaces differ between
      implementations (e.g., `set_program()` in WebApp → `Program()` in POUI).

    :param config_path: Path to config.json file
    :param inst_webapp: Optional WebappInternal instance for injection
    :param inst_poui: Optional PouiInternal instance for injection

    Note: Driver instances are created lazily only when needed.
    """

    def __init__(self, config_path: str = "", inst_webapp=None, inst_poui=None):
        self.config = ConfigLoader()
        self._config_path = config_path
        self.__webapp = None
        self.__poui = None
        self.set_webapp(inst_webapp)
        self.set_poui(inst_poui)

    def set_webapp(self, inst):
        """Set the `WebappInternal` instance to be used.

        Allows injection at initialization or later. Passing None is valid
        and will trigger lazy initialization when needed.

        :param inst: WebappInternal instance or None for lazy initialization
        """
        self.__webapp = inst

    def set_poui(self, inst):
        """Set the `PouiInternal` instance to be used.

        Allows injection at initialization or later. Passing None is valid
        and will trigger lazy initialization when needed.

        :param inst: PouiInternal instance or None for lazy initialization
        """
        self.__poui = inst

    def _ensure_webapp(self):
        """Get (or lazily create) the `WebappInternal` instance.

        Returns:
        - Active `WebappInternal` instance ready for use.
        """
        if self.__webapp is None:
            from tir.technologies.webapp_internal import WebappInternal
            self.__webapp = WebappInternal(self._config_path, autostart=False)
        return self.__webapp

    def _ensure_poui(self):
        """Get (or lazily create) the `PouiInternal` instance.

        Returns:
        - Active `PouiInternal` instance ready for use.
        """
        if self.__poui is None:
            from tir.technologies.poui_internal import PouiInternal
            self.__poui = PouiInternal(self._config_path, autostart=False)
        return self.__poui
    
    def _route_to_driver(self, condition_fn):
        """Roteia para o driver apropriado baseado em uma função de condição.
        
        :param condition_fn: Função que retorna True para POUI, False para WebApp
        :return: Driver selecionado (POUI ou WebApp)
        """
        return self._ensure_poui() if condition_fn() else self._ensure_webapp()

    def Program(self, program_name: str):
        """Open/select a Protheus program routine.

        Parameters:
        - program_name: Routine/program code (e.g., 'OMSA010').

        Behavior:
        - Routes the call to the active implementation (POUI/WebApp).
        - When `new_home` is enabled and `initial_program` is 'SIGAADV',
            runs auxiliary WebApp routines to close accessory screens
            (warnings, currency conversion, news) after opening the routine.
        """
        drv = self._route_to_driver(lambda: self.config.new_home)
        drv.Program(program_name)

        if self.config.new_home and self.config.initial_program.lower() == 'sigaadv':
            self._ensure_webapp().close_warning_screen_after_routine()
            self._ensure_webapp().close_coin_screen_after_routine()
            self._ensure_webapp().close_news_screen_after_routine()


    def set_program(self, program_name: str):
        """Set the current routine without executing additional flows.

        Parameters:
        - program_name: Routine/program code.

        Notes:
        - In POUI, delegates to `Program` to keep implementation compatibility.
        - In WebApp, uses native `set_program` when available.
        """
        if self.config.new_home:
            self._ensure_poui().Program(program_name)
        else:
            self._ensure_webapp().set_program(program_name)