
from tir.technologies.core.config import ConfigLoader

class Adapter:

    def __init__(self, config_path: str = "", inst_webapp=None, inst_poui=None):
        # Avoid importing internals here to reduce coupling; instances are injected.
        self.config = ConfigLoader()
        self._config_path = config_path
        self.__webapp = inst_webapp
        self.__poui = inst_poui

    def set_webapp(self, inst):
        self.__webapp = inst

    def set_poui(self, inst):
        self.__poui = inst

    def _ensure_webapp(self):
        if self.__webapp is None:
            from tir.technologies.webapp_internal import WebappInternal
            self.__webapp = WebappInternal(self._config_path, autostart=False)
        return self.__webapp

    def _ensure_poui(self):
        if self.__poui is None:
            from tir.technologies.poui_internal import PouiInternal
            self.__poui = PouiInternal(self._config_path, autostart=False)
        return self.__poui

    def _active(self):
        return self._ensure_poui() if self.config.new_home else self._ensure_webapp()

    def Program(self, program_name: str):
        drv = self._active()
        drv.Program(program_name)

        if self.config.new_home and self.config.initial_program.lower() == 'sigaadv':
            self._ensure_webapp().close_warning_screen_after_routine()
            self._ensure_webapp().close_coin_screen_after_routine()
            self._ensure_webapp().close_news_screen_after_routine()


    def set_program(self, program_name: str):
        if self.config.new_home:
            self._ensure_poui().Program(program_name)
        else:
            self._ensure_webapp().set_program(program_name)