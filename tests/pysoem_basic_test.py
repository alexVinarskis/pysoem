
import dataclasses
import pytest
import pysoem


BECKHOFF_VENDOR_ID = 0x0002
EK1100_PRODUCT_CODE = 0x044c2c52
EL3002_PRODUCT_CODE = 0x0bba3052
EL1259_PRODUCT_CODE = 0x04eb3052


@dataclasses.dataclass
class Device:
    name: str
    vendor_id: int
    product_code: int


def test_version():
    assert isinstance(pysoem.__version__, str)


def test_find_adapters():
    pysoem.find_adapters()


def test_config_function_exception(pysoem_env):
    """Check if an exception in a config_func callback causes config_map to fail"""
    class DummyException(Exception):
        pass

    def el1259_config_func(slave_pos):
        raise DummyException()

    pysoem_env.config_init()
    pysoem_env.el1259_config_func = el1259_config_func

    with pytest.raises(DummyException) as excinfo:
        pysoem_env.config_map()
    assert isinstance(excinfo.value, DummyException)


def test_master_context_manager(ifname):
    """Quick check if the open() function context manager works as expected."""
    with pysoem.open(ifname) as master:
        if master.config_init() > 0:
            expected_slave_layout = {
                0: Device('XMC43-Test-Device', 0, 0x12783456),
                1: Device('EK1100', BECKHOFF_VENDOR_ID, EK1100_PRODUCT_CODE),
                2: Device('EL3002', BECKHOFF_VENDOR_ID, EL3002_PRODUCT_CODE),
                3: Device('EL1259', BECKHOFF_VENDOR_ID, EL1259_PRODUCT_CODE),
            }
            for i, slave in enumerate(master.slaves):
                assert slave.man == expected_slave_layout[i].vendor_id
                assert slave.id == expected_slave_layout[i].product_code
        else:
            pytest.fail()


setup_func_was_called = False
def test_setup_function(pysoem_env):
    """Check if the new setup_func works as intended."""

    def el1259_setup_func(slave):
        global setup_func_was_called
        assert slave.id == EL1259_PRODUCT_CODE
        setup_func_was_called = True


    pysoem_env.config_init()
    pysoem_env.el1259_setup_func = el1259_setup_func

    pysoem_env.config_map()  # el1259_setup_func is expected to be called here

    assert setup_func_was_called