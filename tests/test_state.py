from tofupy import State, Tofu


def test_state(tofu_existing):
    workspace = Tofu(cwd=tofu_existing)
    state = workspace.state()
    assert isinstance(state, State)

    assert state.outputs["site_data"].type == "string"
    assert len(state.outputs["site_data"].value) >= 0
    assert state.outputs["site_data"].sensitive is False

    resources = state.root_module.resources
    assert len(resources) == 2
    assert resources["data.http.site"].type == "http"

    assert state.serial >= 0
    assert isinstance(state.lineage, str)
    assert len(state.lineage) >= 0
