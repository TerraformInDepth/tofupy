from tofupy import Diagnostic, Tofu, Validate


def test_validate_not_initiated(tofu_rlm):
    workspace = Tofu(cwd=tofu_rlm)
    validate = workspace.validate()
    assert isinstance(validate, Validate)

    assert validate.valid is False
    assert validate.error_count == 1
    assert validate.warning_count == 0

    first_diagnostic = validate.diagnostics[0]

    assert isinstance(first_diagnostic, Diagnostic)
    assert first_diagnostic.severity == "error"
    assert first_diagnostic.summary == "Missing required provider"
    assert "hashicorp/http" in first_diagnostic.detail


def test_validate_existing(tofu_existing):
    workspace = Tofu(cwd=tofu_existing)
    validate = workspace.validate()
    assert isinstance(validate, Validate)

    assert validate.valid is True
    assert validate.error_count == 0
    assert validate.warning_count == 0
    assert len(validate.diagnostics) == 0
