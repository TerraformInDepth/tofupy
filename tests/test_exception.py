import pytest

from tofupy import Tofu


def test_run_exception(tofu_rlm):
    with pytest.raises(RuntimeError) as e:  # noqa: F841
        tofu = Tofu(cwd=tofu_rlm)
        tofu.init(extra_args=["--invalid-arg"])
