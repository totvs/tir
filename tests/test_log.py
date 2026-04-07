import tempfile
from pathlib import Path
import types
import uuid

import pytest

import importlib.util

# Load `Log` directly from file to avoid importing package-level dependencies
repo_root = Path(__file__).resolve().parents[1]
log_path = repo_root / 'tir' / 'technologies' / 'core' / 'log.py'
spec = importlib.util.spec_from_file_location('tir_log', str(log_path))
mod = importlib.util.module_from_spec(spec)

# Inject minimal tir package stubs to avoid importing heavy dependencies during tests
import sys
pkg = types.ModuleType('tir')
sys.modules['tir'] = pkg
sys.modules['tir.technologies'] = types.ModuleType('tir.technologies')
sys.modules['tir.technologies.core'] = types.ModuleType('tir.technologies.core')

# Minimal ConfigLoader stub
cfg_mod = types.ModuleType('tir.technologies.core.config')
class DummyConfig:
    def __init__(self, path=None):
        self.issue = ''
        self.execution_id = ''
        self.country = 'BRA'
        self.release = ''
        self.logurl1 = ''
        self.logurl2 = ''
        self.smart_test = False
        self.log_http = ''
        self.num_exec = None
        self.api_url = ''
        self.api_url_ip = ''
        self.api_json_path = str(repo_root / 'Log')
        self.debug_log = False
cfg_mod.ConfigLoader = lambda path=None: DummyConfig(path)
sys.modules['tir.technologies.core.config'] = cfg_mod

# Minimal logging_config stub
logcfg_mod = types.ModuleType('tir.technologies.core.logging_config')
import logging
def logger():
    return logging.getLogger('test_logger')
logcfg_mod.logger = logger
sys.modules['tir.technologies.core.logging_config'] = logcfg_mod

spec.loader.exec_module(mod)
Log = mod.Log


def make_log_with_cfg(tmp_dir: Path):
    l = Log(user='tester', station='station')
    class Cfg:
        pass
    cfg = Cfg()
    cfg.log_http = str(tmp_dir)
    cfg.country = 'BRA'
    cfg.release = '1.0'
    cfg.issue = 'ISS'
    cfg.execution_id = 'EID'
    cfg.debug_log = False
    l.config = cfg
    return l


def test_diagnostic_io_reports(tmp_path):
    l = make_log_with_cfg(tmp_path)
    res = l.diagnostic_io(tmp_path)
    assert 'user' in res
    assert 'target' in res
    assert res['exists'] is True
    assert isinstance(res['readable'], bool)
    assert isinstance(res['writable'], bool)


def test_take_screenshot_writes_file(tmp_path):
    l = make_log_with_cfg(tmp_path)

    # Prepare a fake driver that actually writes the file so we can assert existence
    captured = []
    def save_screenshot(path):
        captured.append(path)
        Path(path).write_text('screenshot')
        return True

    driver = types.SimpleNamespace()
    driver.save_screenshot = save_screenshot

    screenshot_name = 'my_test'
    stack_item = f"testcase_{uuid.uuid4().hex[:6]}"

    l.take_screenshot_log(driver, description=screenshot_name, stack_item=stack_item)

    testsuite = l.get_file_name("testsuite")
    folder_path = Path(l.config.log_http, l.config.country, l.release, l.config.issue, l.config.execution_id, testsuite)
    # Assert that driver was called and file was created at that path
    assert captured, "Driver.save_screenshot was not called"
    written_path = Path(captured[0])
    assert written_path.exists()


def test_take_screenshot_fallback_on_write_fail(tmp_path, monkeypatch):
    l = make_log_with_cfg(tmp_path)

    # Simulate write failure (e.g., directory read-only)
    def failing_save_screenshot(path):
        raise PermissionError("Simulated write fail")

    driver = types.SimpleNamespace()
    driver.save_screenshot = failing_save_screenshot

    # Monkeypatch tempfile.gettempdir to a controlled dir
    temp_dir = tmp_path / 'fallback'
    temp_dir.mkdir()
    monkeypatch.setattr('tempfile.gettempdir', lambda: str(temp_dir))

    # Should not crash; should log and continue
    l.take_screenshot_log(driver, description='fail_test', stack_item='testcase_123')
    # Verify if file was created in fallback (if applicable)
