from pathlib import Path

from tofupy import Tofu


def test_init(tofu_existing):
    workspace = Tofu(cwd=tofu_existing)
    init_directory = Path(workspace.cwd) / ".terraform"
    assert init_directory.exists()
