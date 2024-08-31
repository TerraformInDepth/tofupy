from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Diagnostic:
    # Format: https://developer.hashicorp.com/terraform/internals/json-format#diagnostic-representation
    data: Dict[str, Any] = field(repr=False)

    severity: str = field(init=False)
    summary: str = field(init=False)
    detail: str = field(init=False)

    def __post_init__(self):
        self.severity = self.data.get("severity")
        self.summary = self.data.get("summary")
        self.detail = self.data.get("detail")


@dataclass
class Validate:
    # Format: https://developer.hashicorp.com/terraform/cli/commands/validate#json
    data: Dict[str, Any] = field(repr=False)

    valid: bool = field(init=False)
    diagnostics: List[Diagnostic] = field(init=False)
    error_count: int = field(init=False)
    warning_count: int = field(init=False)

    def __post_init__(self):
        self.valid = bool(self.data.get("valid"))
        self.diagnostics = [
            Diagnostic(diagnostic) for diagnostic in self.data.get("diagnostics", [])
        ]
        self.error_count = int(self.data.get("error_count"))
        self.warning_count = int(self.data.get("warning_count"))


@dataclass
class Resource:
    # Format: https://developer.hashicorp.com/terraform/internals/json-format#values-representation
    data: Dict[str, Any] = field(repr=False)

    address: str = field(init=False)
    mode: str = field(init=False)
    type: str = field(init=False)
    name: str = field(init=False)
    index: int | None = field(init=False)
    schema_version: int = field(init=False)
    provider_name: str = field(init=False)
    values: Dict[str, Any] = field(init=False)
    sensitive_values: Dict[str, bool] = field(init=False)

    def __post_init__(self):
        self.address = self.data.get("address")
        self.mode = self.data.get("mode")
        self.type = self.data.get("type")
        self.name = self.data.get("name")
        self.index = self.data.get("index")
        self.schema_version = self.data.get("schema_version")
        self.provider_name = self.data.get("provider_name")
        self.values = self.data.get("values")


@dataclass
class Module:
    # Format: https://developer.hashicorp.com/terraform/internals/json-format#values-representation
    data: Dict[str, Any] = field(repr=False)

    address: str | None = field(init=False)
    resources: Dict[str, Resource] = field(init=False)
    child_modules: List[Dict[str, "Module"]] = field(init=False)

    def __post_init__(self):
        self.address = self.data.get("address")

        self.resources = {}
        for resource in self.data.get("resources", []):
            self.resources[resource.get("address")] = Resource(resource)

        self.child_modules = {}
        for child_module in self.data.get("child_modules", []):
            self.child_modules[child_module.get("address")] = Module(child_module)


@dataclass
class Output:
    # Format: https://developer.hashicorp.com/terraform/internals/json-format#values-representation
    data: Dict[str, Any] = field(repr=False)

    value: Any = field(init=False)
    type: str = field(init=False)
    sensitive: bool = field(init=False)

    def __post_init__(self):
        self.value = self.data.get("value")
        self.type = self.data.get("type")
        self.sensitive = self.data.get("sensitive")


@dataclass
class State:
    # Format: https://developer.hashicorp.com/terraform/internals/json-format#state-representation
    # Format: https://developer.hashicorp.com/terraform/internals/json-format#values-representation
    data: Dict[str, Any] = field(repr=False)
    serial: int | None = None
    lineage: str | None = None

    version: int = field(init=False)
    terraform_version: str = field(init=False)

    root_module: Module = field(init=False)
    outputs: Dict[str, Output] = field(init=False)

    def __post_init__(self):
        self.version = self.data.get("version")
        self.terraform_version = self.data.get("terraform_version")

        values = self.data.get("values")

        self.outputs = {}
        for name, value in values.get("outputs", {}).items():
            self.outputs[name] = Output(value)

        root_module = values.get("root_module")
        if root_module:
            self.root_module = Module(root_module)
        else:
            self.root_module = None


@dataclass
class Change:
    # Format: https://developer.hashicorp.com/terraform/internals/json-format#change-representation
    data: Dict[str, Any] = field(repr=False)

    actions: List[str] = field(init=False)
    before: Dict[str, Any] | None = field(init=False)
    after: Dict[str, Any] | None = field(init=False)

    before_sensitive: Dict[str, bool] | bool = field(init=False)
    after_sensitive: Dict[str, bool] | bool = field(init=False)

    after_unknown: Dict[str, bool] = field(init=False)

    def __post_init__(self):
        self.actions = self.data.get("actions", [])

        before = self.data.get("before")
        if before is None:
            self.before = None
        else:
            self.before_root_module

        self.before = self.data.get("before")
        self.after = self.data.get("after")

        self.before_sensitive = self.data.get("before_sensitive")
        self.after_sensitive = self.data.get("after_sensitive")

        self.after_unknown = self.data.get("after_unknown")


@dataclass
class ChangeContainer:
    # Format: https://developer.hashicorp.com/terraform/internals/json-format#change-representation
    data: Dict[str, Any] = field(repr=False)

    address: str = field(init=False)
    previous_address: str | None = field(init=False)
    module_address: str | None = field(init=False)
    mode: str = field(init=False)
    type: str = field(init=False)
    name: str = field(init=False)
    index: int | None = field(init=False)
    provider_name: str | None = field(init=False)

    disposed: str | None = field(init=False)
    action_reason: str = field(init=False)

    change: Change = field(init=False)

    def __post_init__(self):
        self.address = self.data.get("address")
        self.previous_address = self.data.get("address")
        self.module_address = self.data.get("address")
        self.mode = self.data.get("mode")
        self.type = self.data.get("type")
        self.name = self.data.get("name")
        self.index = self.data.get("index")
        self.provider_name = self.data.get("provider_name")
        self.disposed = self.data.get("disposed")
        self.action_reason = self.data.get("action_reason")
        self.change = Change(self.data.get("change"))


@dataclass
class Plan:
    # Format: https://developer.hashicorp.com/terraform/internals/json-format#plan-representation
    data: Dict[str, Any] = field(repr=False)

    resource_changes: Dict[str, ChangeContainer] = field(init=False)
    resource_drift: Dict[str, ChangeContainer] = field(init=False)
    output_changes: Dict[str, Change] = field(init=False)
    prior_state: State = field(init=False)

    planned_root_module: Module = field(init=False)
    planned_outputs: Dict[str, Output] = field(init=False)
    relevant_attributes: Dict[str, List[str]] = field(init=False)

    format_version: str = field(init=False)
    terraform_version: str = field(init=False)
    applyable: bool = field(init=False)
    complete: bool = field(init=False)
    errored: bool = field(init=False)
    variables: Dict[str, Any] = field(init=False)

    def __post_init__(self):
        self.format_version = self.data.get("format_version")
        self.terraform_version = self.data.get("terraform_version")
        self.applyable = self.data.get("applyable")
        self.complete = self.data.get("complete")
        self.errored = self.data.get("errored")

        self.variables = {}
        for variable_key, variable_data in self.data.get("variables", {}).items():
            self.variables[variable_key] = variable_data["value"]

        planned_values = self.data.get("planned_values", {})
        self.planned_root_module = Module(planned_values.get("root_module"))

        self.planned_outputs = {}
        for output_name, output_data in self.data.get("output_changes", {}).items():
            self.planned_outputs[output_name] = Output(output_data)

        self.relevant_attributes = {}
        for attribute in self.data.get("relevant_attributes", []):
            self.relevant_attributes[attribute["resource"]] = attribute["attribute"]

        self.prior_state = State(self.data.get("prior_state"))

        self.resource_changes = {}
        for resource_change in self.data.get("resource_changes", []):
            address = resource_change.get("address")
            self.resource_changes[address] = ChangeContainer(resource_change)

        self.resource_drift = {}
        for resource_drift in self.data.get("resource_drift", []):
            address = resource_drift.get("address")
            self.resource_drift[address] = ChangeContainer(resource_drift)

        self.output_changes = {}
        for output_name, output_change in self.data.get("output_changes", {}).items():
            self.output_changes[output_name] = Change(output_change)


@dataclass
class StreamLog:
    # Format: https://developer.hashicorp.com/terraform/internals/machine-readable-ui
    data: List[Dict[str, Any]] = field(repr=False)

    terraform_version: str = field(init=False)
    outputs: Dict[str, Output] = field(init=False)
    added: int = field(init=False)
    changed: int = field(init=False)
    removed: int = field(init=False)
    imported: int = field(init=False)
    operation: str = field(init=False)
    errors: List[Diagnostic] = field(init=False)
    warnings: List[Diagnostic] = field(init=False)

    def __post_init__(self):
        self.outputs = {}
        self.errors = []
        self.warnings = []
        for line in self.data:
            if line.get("type") == "version":
                self.terraform_version = line.get("version")
                continue

            if line.get("type") == "diagnostic":
                if line.get("@level") == "error":
                    self.errors.append(Diagnostic(line))
                if line.get("@level") == "warning":
                    self.warnings.append(Diagnostic(line))
                continue

            if line.get("type") == "outputs":
                for key, value in line.get("outputs").items():
                    self.outputs[key] = Output(value)
                continue

            if line.get("type") == "change_summary":
                changes = line.get("changes", {})
                self.added = changes.get("add", 0)
                self.changed = changes.get("change", 0)
                self.removed = changes.get("remove", 0)
                self.imported = changes.get("import", 0)
                self.operation = changes.get("operation", None)
                continue


class PlanLog(StreamLog):
    pass


class ApplyLog(PlanLog):
    pass
