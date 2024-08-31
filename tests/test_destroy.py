from tofupy import ApplyLog, Tofu


def test_destroy(tofu_existing):
    workspace = Tofu(cwd=tofu_existing)
    destroy = workspace.destroy()
    assert isinstance(destroy, ApplyLog)
    assert destroy.removed == 1
    assert destroy.operation == "apply"
