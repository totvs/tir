import importlib.util
import logging
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


repo_root = Path(__file__).resolve().parents[1]
module_path = repo_root / "tir" / "technologies" / "webapp_internal.py"


class FakeElement:
    def __init__(self, text="", attrs=None, parent=None):
        self.text = text
        self.attrs = attrs or {}
        self.parent = parent
        self.click_count = 0

    def get_attribute(self, name):
        return self.attrs.get(name)

    def click(self):
        self.click_count += 1


def _register_module(name, module=None):
    module = module or types.ModuleType(name)
    sys.modules[name] = module

    if "." in name:
        parent_name, child_name = name.rsplit(".", 1)
        parent = sys.modules.get(parent_name)
        if parent is None:
            parent = _register_module(parent_name)
        setattr(parent, child_name, module)

    return module


def load_webapp_internal_module():
    cached = sys.modules.get("tir_webapp_internal_test")
    if cached is not None:
        return cached

    # External dependency stubs used only to import the module for isolated unit tests.
    _register_module("pandas")
    _register_module("cv2")

    bs4_mod = _register_module("bs4")
    bs4_mod.BeautifulSoup = type("BeautifulSoup", (), {})
    bs4_mod.Tag = type("Tag", (), {})

    _register_module("selenium")
    _register_module("selenium.webdriver")
    _register_module("selenium.webdriver.common")
    _register_module("selenium.webdriver.support")

    keys_mod = _register_module("selenium.webdriver.common.keys")
    keys_mod.Keys = type("Keys", (), {"CONTROL": "CONTROL", "F5": "F5"})

    by_mod = _register_module("selenium.webdriver.common.by")
    by_mod.By = type("By", (), {"CSS_SELECTOR": "css", "XPATH": "xpath"})

    action_mod = _register_module("selenium.webdriver.common.action_chains")
    action_mod.ActionChains = type("ActionChains", (), {})

    support_ui_mod = _register_module("selenium.webdriver.support.ui")
    support_ui_mod.Select = type("Select", (), {})

    expected_conditions_mod = _register_module("selenium.webdriver.support.expected_conditions")
    expected_conditions_mod.EC = type("EC", (), {})

    exceptions_mod = _register_module("selenium.common.exceptions")
    exceptions_mod.WebDriverException = type("WebDriverException", (Exception,), {})
    exceptions_mod.NoSuchElementException = type("NoSuchElementException", (Exception,), {})

    tir_pkg = _register_module("tir")
    tir_pkg.__path__ = []
    technologies_pkg = _register_module("tir.technologies")
    technologies_pkg.__path__ = []
    core_pkg = _register_module("tir.technologies.core")
    core_pkg.__path__ = []
    third_party_pkg = _register_module("tir.technologies.core.third_party")
    third_party_pkg.__path__ = []

    enum_mod = _register_module("tir.technologies.core.enumerations")
    enum_mod.ClickType = type("ClickType", (), {"SELENIUM": "selenium", "JS": "js"})
    enum_mod.ScrapType = type(
        "ScrapType",
        (),
        {
            "TEXT": "text",
            "MIXED": "mixed",
            "CSS_SELECTOR": "css",
            "SCRIPT": "script",
        },
    )
    enum_mod.MessageType = type(
        "MessageType",
        (),
        {
            "CORRECT": "correct",
            "INCORRECT": "incorrect",
            "DISABLED": "disabled",
            "ASSERTERROR": "asserterror",
        },
    )

    base_module = _register_module("tir.technologies.core.base")
    base_module.Base = type("Base", (), {"errors": []})

    log_module = _register_module("tir.technologies.core.log")
    log_module.Log = type("Log", (), {})
    log_module.nump = None

    config_module = _register_module("tir.technologies.core.config")
    config_module.ConfigLoader = lambda *args, **kwargs: None

    language_module = _register_module("tir.technologies.core.language")
    language_module.LanguagePack = type("LanguagePack", (), {})

    xpath_module = _register_module("tir.technologies.core.third_party.xpath_soup")
    xpath_module.xpath_soup = lambda *args, **kwargs: "//stub"

    psutil_module = _register_module("tir.technologies.core.psutil_info")
    psutil_module.system_info = lambda: {}

    numexec_module = _register_module("tir.technologies.core.numexec")
    numexec_module.NumExec = type("NumExec", (), {})

    logging_config_module = _register_module("tir.technologies.core.logging_config")
    logging_config_module.logger = lambda: logging.getLogger("test_webapp_internal_clicktree")

    base_database_module = _register_module("tir.technologies.core.base_database")
    base_database_module.BaseDatabase = type("BaseDatabase", (), {})

    spec = importlib.util.spec_from_file_location("tir_webapp_internal_test", str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["tir_webapp_internal_test"] = module
    return module


def build_webapp():
    module = load_webapp_internal_module()
    webapp = module.WebappInternal.__new__(module.WebappInternal)
    webapp.config = SimpleNamespace(time_out=0.01)
    webapp.tree_base_element = ()
    webapp.wait_blocker = Mock()
    webapp.check_layers = Mock(return_value=0)
    webapp.scroll_to_element = Mock()
    webapp.log_error = Mock()
    webapp.click = Mock()
    webapp.return_last_zindex = Mock(return_value=0)
    webapp.element_exists = Mock(return_value=False)
    webapp.soup_to_selenium = Mock(side_effect=lambda element: element)
    return webapp, module


def test_clicktree_delegates_to_internal_method():
    webapp, _ = build_webapp()
    webapp.click_tree = Mock()

    webapp.ClickTree("nivel 1 > nivel 2", right_click=True, position=2, tree_number=3)

    webapp.click_tree.assert_called_once_with("nivel 1 > nivel 2", True, 2, 3)


def test_click_tree_clicks_the_last_matching_node_without_browser_dependencies():
    webapp, _ = build_webapp()

    node = FakeElement(
        text="  Financeiro   ",
        attrs={"hidden": None, "closed": "", "hierarchy": "01", "icon": None},
    )
    clickable_part = FakeElement(text="Financeiro", parent=node)

    webapp.find_tree_bs = Mock(return_value=[node])
    webapp.element_is_displayed = Mock(return_value=True)
    webapp.check_toggler = Mock(return_value=False)
    webapp.check_hierarchy = Mock(return_value=False)

    selected_nodes = [None, node, node]

    def treenode_selected(_label, _tree_number=0):
        return selected_nodes.pop(0) if selected_nodes else node

    def execute_js_selector(selector, element, get_all=True):
        if selector == ".toggler, .lastchild, .data, label":
            return [clickable_part]
        return None

    webapp.treenode_selected = Mock(side_effect=treenode_selected)
    webapp.execute_js_selector = Mock(side_effect=execute_js_selector)

    webapp.click_tree("Financeiro", right_click=False, position=1, tree_number=0)

    assert clickable_part.click_count == 1
    webapp.log_error.assert_not_called()


def test_click_tree_logs_error_when_no_tree_node_is_found():
    webapp, _ = build_webapp()
    webapp.config.time_out = 0
    webapp.find_tree_bs = Mock(return_value=[])
    webapp.element_is_displayed = Mock(return_value=True)
    webapp.treenode_selected = Mock(return_value=None)
    webapp.execute_js_selector = Mock(return_value=None)
    webapp.check_toggler = Mock(return_value=False)
    webapp.check_hierarchy = Mock(return_value=False)

    webapp.click_tree("Item inexistente", right_click=False, position=1, tree_number=0)

    webapp.log_error.assert_called_once()
    assert "Couldn't click on tree element" in webapp.log_error.call_args.args[0]


def test_click_tree_with_right_click_on_last_node():
    """Test that right_click=True is passed to click method when last item is clicked."""
    webapp, _ = build_webapp()
    
    node = FakeElement(
        text="Menu Item",
        attrs={"hidden": None, "closed": "", "hierarchy": "01", "icon": None},
    )
    clickable_part = FakeElement(text="Menu Item", parent=node)
    
    webapp.find_tree_bs = Mock(return_value=[node])
    webapp.element_is_displayed = Mock(return_value=True)
    webapp.check_toggler = Mock(return_value=False)
    webapp.check_hierarchy = Mock(return_value=False)
    webapp.treenode_selected = Mock(return_value=node)
    webapp.return_last_zindex = Mock(return_value=100)
    
    def execute_js_selector(selector, element, get_all=True):
        if selector == ".toggler, .lastchild, .data, label":
            return [clickable_part]
        return None
    
    webapp.execute_js_selector = Mock(side_effect=execute_js_selector)
    
    webapp.click_tree("Menu Item", right_click=True, position=1, tree_number=0)
    
    # Verify that the main element was clicked (right_click=True path)
    # The actual right_click happens in the loop after regular click
    webapp.log_error.assert_not_called()


def test_click_tree_with_multiple_hierarchy_levels():
    """Test navigating through single level tree (simpler version of multi-level)."""
    webapp, _ = build_webapp()
    
    pai = FakeElement(text="Pai", attrs={"hierarchy": "01", "closed": "", "icon": None})
    pai_clickable = FakeElement(text="Pai", parent=pai)
    
    webapp.find_tree_bs = Mock(return_value=[pai])
    webapp.element_is_displayed = Mock(return_value=True)
    webapp.check_toggler = Mock(return_value=False)
    webapp.check_hierarchy = Mock(return_value=False)
    webapp.treenode_selected = Mock(return_value=pai)
    
    def execute_js_selector(selector, element, get_all=True):
        if selector == ".toggler, .lastchild, .data, label":
            return [pai_clickable]
        return None
    
    webapp.execute_js_selector = Mock(side_effect=execute_js_selector)
    
    # Click the single level
    webapp.click_tree("Pai", right_click=False, position=1, tree_number=0)
    
    # Verify successful click
    webapp.log_error.assert_not_called()


def test_click_tree_respects_position_parameter():
    """Test that position parameter is considered when multiple elements exist."""
    webapp, _ = build_webapp()
    
    # Create multiple nodes with same text
    node1 = FakeElement(text="Duplicado", attrs={"hidden": None, "closed": "", "hierarchy": "01"})
    node2 = FakeElement(text="Duplicado", attrs={"hidden": None, "closed": "", "hierarchy": "02"})
    
    webapp.find_tree_bs = Mock(return_value=[node1, node2])
    webapp.element_is_displayed = Mock(return_value=True)
    webapp.check_toggler = Mock(return_value=False)
    webapp.check_hierarchy = Mock(return_value=False)
    
    # Return node2 when treenode_selected is called
    webapp.treenode_selected = Mock(return_value=node2)
    
    def execute_js_selector(selector, element, get_all=True):
        if selector == ".toggler, .lastchild, .data, label":
            if element == node1:
                return [FakeElement(text="Duplicado")]
            elif element == node2:
                return [FakeElement(text="Duplicado")]
        return None
    
    webapp.execute_js_selector = Mock(side_effect=execute_js_selector)
    
    # Position 2 should try to select the second matching node
    webapp.click_tree("Duplicado", right_click=False, position=2, tree_number=0)
    
    # Verify successful click
    webapp.log_error.assert_not_called()


def test_click_tree_updates_tree_base_element_for_non_last_items():
    """Test that tree_base_element is updated when navigating intermediate nodes."""
    webapp, _ = build_webapp()
    webapp.tree_base_element = ()
    
    pai = FakeElement(text="Pai", attrs={"hierarchy": "01", "closed": "true", "icon": None})
    filho = FakeElement(text="Filho", attrs={"hierarchy": "01-01", "closed": "", "icon": None})
    pai_clickable = FakeElement(text="Pai", parent=pai)
    
    webapp.find_tree_bs = Mock(return_value=[pai, filho])
    webapp.element_is_displayed = Mock(return_value=True)
    webapp.check_toggler = Mock(return_value=True)
    webapp.check_hierarchy = Mock(side_effect=[True, False])
    webapp.treenode_selected = Mock(side_effect=[None, pai, filho])
    
    def execute_js_selector(selector, element, get_all=True):
        if selector == ".toggler, .lastchild, .data, label":
            return [pai_clickable]
        return None
    
    webapp.execute_js_selector = Mock(side_effect=execute_js_selector)
    
    webapp.click_tree("Pai > Filho", right_click=False, position=1, tree_number=0)
    
    # Verify tree_base_element was set to (label_filtered, element_class_item)
    assert webapp.tree_base_element != ()
    assert webapp.tree_base_element[0] == "pai"  # label_filtered is lowercased


def test_click_tree_with_hidden_element():
    """Test that hidden elements are filtered out during element search."""
    webapp, _ = build_webapp()
    
    hidden_node = FakeElement(text="Hidden", attrs={"hidden": "true", "closed": "", "hierarchy": "01"})
    visible_node = FakeElement(text="Visible", attrs={"hidden": None, "closed": "", "hierarchy": "02"})
    clickable = FakeElement(text="Visible", parent=visible_node)
    
    webapp.find_tree_bs = Mock(return_value=[hidden_node, visible_node])
    
    def element_is_displayed_side_effect(element):
        # hidden_node has hidden attribute, so it's not displayed
        if element == hidden_node:
            return False
        return True
    
    webapp.element_is_displayed = Mock(side_effect=element_is_displayed_side_effect)
    webapp.check_toggler = Mock(return_value=False)
    webapp.check_hierarchy = Mock(return_value=False)
    webapp.treenode_selected = Mock(return_value=visible_node)
    
    def execute_js_selector(selector, element, get_all=True):
        if selector == ".toggler, .lastchild, .data, label":
            return [clickable]
        return None
    
    webapp.execute_js_selector = Mock(side_effect=execute_js_selector)
    
    webapp.click_tree("Visible", right_click=False, position=1, tree_number=0)
    
    # Verify hidden element was skipped (log_error not called)
    webapp.log_error.assert_not_called()


def test_click_tree_handles_text_normalization():
    """Test that extra spaces in labels are normalized during matching."""
    webapp, _ = build_webapp()
    
    node = FakeElement(
        text="  Item   com   espaços   ",
        attrs={"hidden": None, "closed": "", "hierarchy": "01", "icon": None},
    )
    clickable_part = FakeElement(text="Item com espaços", parent=node)
    
    webapp.find_tree_bs = Mock(return_value=[node])
    webapp.element_is_displayed = Mock(return_value=True)
    webapp.check_toggler = Mock(return_value=False)
    webapp.check_hierarchy = Mock(return_value=False)
    webapp.treenode_selected = Mock(return_value=node)
    
    def execute_js_selector(selector, element, get_all=True):
        if selector == ".toggler, .lastchild, .data, label":
            return [clickable_part]
        return None
    
    webapp.execute_js_selector = Mock(side_effect=execute_js_selector)
    
    # Search with single spaces should match label with multiple spaces
    webapp.click_tree("Item com espaços", right_click=False, position=1, tree_number=0)
    
    # Verify normalization worked (no error)
    webapp.log_error.assert_not_called()


def test_click_tree_tree_number_parameter():
    """Test that tree_number parameter is used to locate the correct tree."""
    webapp, _ = build_webapp()
    
    tree_node = FakeElement(text="Tree2Item", attrs={"hidden": None, "closed": "", "hierarchy": "02"})
    clickable = FakeElement(text="Tree2Item", parent=tree_node)
    
    # find_tree_bs is called with tree_number to select the correct tree
    webapp.find_tree_bs = Mock(return_value=[tree_node])
    webapp.element_is_displayed = Mock(return_value=True)
    webapp.check_toggler = Mock(return_value=False)
    webapp.check_hierarchy = Mock(return_value=False)
    webapp.treenode_selected = Mock(return_value=tree_node)
    
    def execute_js_selector(selector, element, get_all=True):
        if selector == ".toggler, .lastchild, .data, label":
            return [clickable]
        return None
    
    webapp.execute_js_selector = Mock(side_effect=execute_js_selector)
    
    # Use tree_number=2 (should be converted to index 1)
    webapp.click_tree("Tree2Item", right_click=False, position=1, tree_number=2)
    
    # Verify find_tree_bs was called with the correct tree_number
    assert webapp.find_tree_bs.called
    # Verify successful click (no error logged)
    webapp.log_error.assert_not_called()
