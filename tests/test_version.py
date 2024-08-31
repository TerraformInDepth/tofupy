from tofupy import Tofu


def test_version():
    workspace = Tofu()
    assert len(workspace.version) > 0
