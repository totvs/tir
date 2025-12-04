
from tir.technologies.core.config import ConfigLoader

class Adapter:
    """
    Adapter for routing between UI implementations (POUI and WebApp).

    This class exposes a stable interface for scripts, deciding at runtime
    which internal implementation will be triggered based on configuration.

    Goals:
    - Preserve compatibility with existing scripts that import `Webapp`.
    - Avoid unnecessary coupling through dependency injection (instances of
        `WebappInternal`/`PouiInternal` can be provided externally).

    Parameters:
    - config_path: Path to the configuration file (config.json).
    - inst_webapp: Pre-existing instance of `WebappInternal` (optional).
    - inst_poui: Pre-existing instance of `PouiInternal` (optional).

    Behavior:
    - Internal instances are lazily initialized: they are created only when
        a path is selected and there is no corresponding instance yet.
    """

    def __init__(self, config_path: str = "", inst_webapp=None, inst_poui=None):
        self.config = ConfigLoader()
        self._config_path = config_path
        self.__webapp = inst_webapp
        self.__poui = inst_poui

    def set_webapp(self, inst):
        """Set the `WebappInternal` instance to be used.

        Recommended usage: allow injection by whoever orchestrates the lifecycle,
        avoiding that the Adapter takes responsibility for creation in testing
        or reuse scenarios.
        """
        self.__webapp = inst

    def set_poui(self, inst):
        """Set the `PouiInternal` instance to be used.

        Similar to `set_webapp`.
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
        drv = self._ensure_poui() if self.config.new_home else self._ensure_webapp()
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