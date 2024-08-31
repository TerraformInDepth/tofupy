from tofupy import Output, Tofu


def test_output(tofu_existing):
    workspace = Tofu(cwd=tofu_existing)

    outputs = workspace.output()

    assert "site_data" in outputs
    site_data = outputs["site_data"]

    assert isinstance(site_data, Output)
    assert site_data.sensitive is False
    assert site_data.value is not None
    assert site_data.type == "string"
