import os
import shutil
import tempfile
from pathlib import Path

import pytest

from tofupy import Tofu

os.environ["TF_PLUGIN_CACHE_DIR"] = tempfile.mkdtemp()


@pytest.fixture
def tofu_rlm(tmpdir):
    shutil.copytree(
        Path(__file__).parent.absolute() / "module",
        tmpdir,
        dirs_exist_ok=True,
    )
    return tmpdir


@pytest.fixture
def tofu_rlm_error(tmpdir):
    shutil.copytree(
        Path(__file__).parent.absolute() / "module_error",
        tmpdir,
        dirs_exist_ok=True,
    )
    return tmpdir


@pytest.fixture
def tofu_existing(tofu_rlm):
    workspace = Tofu(cwd=tofu_rlm)
    workspace.init()
    workspace.apply()

    return tofu_rlm
