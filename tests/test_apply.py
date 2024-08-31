from tofupy import ApplyLog, Tofu
from tofupy.schema import Diagnostic


def test_apply(tofu_rlm):
    workspace = Tofu(cwd=tofu_rlm)
    workspace.init()
    apply = workspace.apply()
    assert isinstance(apply, ApplyLog)
    assert apply.added == 1
    assert apply.operation == "apply"


def test_apply_handler(tofu_rlm):
    handler_triggered = False

    def handler(event):
        nonlocal handler_triggered
        handler_triggered = True
        return True

    all_handler_triggered = False

    def all_handler(event):
        nonlocal all_handler_triggered
        all_handler_triggered = True
        return True

    workspace = Tofu(cwd=tofu_rlm)
    workspace.init()
    apply = workspace.apply(
        event_handlers={"change_summary": handler, "all": all_handler}
    )
    assert isinstance(apply, ApplyLog)
    assert handler_triggered


def test_apply_error(tofu_rlm_error):
    workspace = Tofu(cwd=tofu_rlm_error)
    workspace.init()
    apply = workspace.apply()

    assert len(apply.errors) > 0
    assert isinstance(apply.errors[0], Diagnostic)
