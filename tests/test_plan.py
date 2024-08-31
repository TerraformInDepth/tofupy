from tofupy import Change, ChangeContainer, Diagnostic, Plan, PlanLog, State, Tofu


def test_plan(tofu_rlm):
    workspace = Tofu(cwd=tofu_rlm)
    workspace.init()
    plan_log, plan = workspace.plan()

    assert isinstance(plan_log, PlanLog)

    assert isinstance(plan, Plan)
    assert "terraform_data.main" in plan.resource_changes

    change_container = plan.resource_changes["terraform_data.main"]
    assert isinstance(change_container, ChangeContainer)
    assert change_container.name == "main"
    assert change_container.type == "terraform_data"
    assert change_container.provider_name == "terraform.io/builtin/terraform"

    change = change_container.change
    assert isinstance(change, Change)
    assert "create" in change.actions
    assert len(change.actions) == 1

    prior_state = plan.prior_state
    assert isinstance(prior_state, State)


def test_plan_handler(tofu_rlm):
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
    plan_log, plan = workspace.plan(
        event_handlers={"change_summary": handler, "all": all_handler}
    )
    assert isinstance(plan_log, PlanLog)
    assert isinstance(plan, Plan)
    assert handler_triggered
    assert all_handler_triggered


def test_plan_error(tofu_rlm_error):
    workspace = Tofu(cwd=tofu_rlm_error)
    workspace.init()
    plan_log, plan = workspace.plan()

    assert isinstance(plan_log, PlanLog)
    assert plan is None

    assert len(plan_log.errors) > 0
    assert isinstance(plan_log.errors[0], Diagnostic)
