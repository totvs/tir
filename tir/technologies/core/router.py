
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
        
        Verifies if the instance has a valid driver. If the driver is invalid
        (closed or None), recreates the instance which will automatically
        get the updated Base.driver.

        Returns:
        - Active `WebappInternal` instance ready for use.
        """
        # Criar instância se não existe ou se o driver está inválido
        if self.__webapp is None or not self._is_driver_active(self.__webapp):
            from tir.technologies.webapp_internal import WebappInternal
            self.__webapp = WebappInternal(self._config_path, autostart=False)
        
        return self.__webapp

    def _ensure_poui(self):
        """Get (or lazily create) the `PouiInternal` instance.
        
        Verifies if the instance has a valid driver. If the driver is invalid
        (closed or None), recreates the instance which will automatically
        get the updated Base.driver.

        Returns:
        - Active `PouiInternal` instance ready for use.
        """
        # Criar instância se não existe ou se o driver está inválido
        if self.__poui is None or not self._is_driver_active(self.__poui):
            from tir.technologies.poui_internal import PouiInternal
            self.__poui = PouiInternal(self._config_path, autostart=False)
        
        return self.__poui
    
    def _is_driver_active(self, instance):
        """Verifica se o driver da instância está ativo e funcional.
        
        :param instance: Instância de WebappInternal ou PouiInternal
        :return: True se o driver está ativo, False caso contrário
        """
        try:
            if not hasattr(instance, 'driver') or instance.driver is None:
                return False
            # Tenta acessar current_url para verificar se a sessão está ativa
            _ = instance.driver.current_url
            return True
        except Exception:
            return False
    
    def _route_to_driver(self, condition_fn):
        """Roteia para o driver apropriado baseado em uma função de condição.
        
        :param condition_fn: Função que retorna True para POUI, False para WebApp
        :return: Driver selecionado (POUI ou WebApp)
        """
        return self._ensure_poui() if condition_fn() else self._ensure_webapp()

    def Program(self, program_name: str):
        drv = self._route_to_driver(lambda: self.config.new_home)
        drv.Program(program_name)

        if self.config.new_home and self.config.initial_program.lower() == 'sigaadv':
            self._ensure_webapp().close_warning_screen_after_routine()
            self._ensure_webapp().close_coin_screen_after_routine()
            self._ensure_webapp().close_news_screen_after_routine()

    def set_program(self, program_name: str):

        drv = self._route_to_driver(lambda: self.config.new_home)
        drv.set_program(program_name)

        if self.config.new_home and self.config.initial_program.lower() == 'sigaadv':
            self._ensure_webapp().close_warning_screen_after_routine()
            self._ensure_webapp().close_coin_screen_after_routine()
            self._ensure_webapp().close_news_screen_after_routine()

    def SetLateralMenu(self, menu_itens, save_input=True, click_menu_functional=False):
        """
        Esse método foi adaptado, pois a função SetLateralMenu ainda
        não foi implementado no POUI.
        """

        if self.config.new_home:
            self._ensure_webapp().config.routine = None
            self._ensure_webapp().config.routine_type = None
            self._ensure_webapp().log_error('Função SetLateralMenu não implementada na nova home.')
        else:            
            self._ensure_webapp().SetLateralMenu(menu_itens, save_input, click_menu_functional)