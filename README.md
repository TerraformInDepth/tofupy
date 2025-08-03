# TofuPy

A comprehensive Python wrapper library for OpenTofu and Terraform that provides a Pythonic interface to infrastructure as code operations.

This project was built as an example for Chapter 11 of [Terraform in Depth](https://mng.bz/QR21) to demonstrate how to wrap the OpenTofu or Terraform binaries for control from Python. Despite being an example, this is an active and maintained open source project suitable for production use.

## Features

- **Full Terraform/OpenTofu Lifecycle Management**: Initialize, validate, plan, apply, and destroy infrastructure
- **Structured Data Models**: Rich Python data classes for all Terraform objects (plans, state, outputs, etc.)
- **Real-time Event Handling**: Stream and handle Terraform execution events as they occur
- **Type Safety**: Full type annotations and structured schemas for all Terraform JSON outputs
- **Cross-Platform**: Works with both OpenTofu and Terraform binaries
- **Production Ready**: Used in real-world scenarios with comprehensive error handling

## Documentation

- [TofuPy](#tofupy)
  - [Features](#features)
  - [Documentation](#documentation)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Core Concepts](#core-concepts)
    - [The Tofu Class](#the-tofu-class)
    - [Structured Data Models](#structured-data-models)
  - [Detailed Usage Examples](#detailed-usage-examples)
    - [Infrastructure Lifecycle Management](#infrastructure-lifecycle-management)
      - [Initialization](#initialization)
      - [Configuration Validation](#configuration-validation)
      - [Planning Changes](#planning-changes)
      - [Applying Changes](#applying-changes)
      - [Managing State](#managing-state)
      - [Getting Outputs](#getting-outputs)
      - [Destroying Infrastructure](#destroying-infrastructure)
    - [Event Handling and Real-time Monitoring](#event-handling-and-real-time-monitoring)
    - [Advanced Use Cases](#advanced-use-cases)
      - [Infrastructure Security Scanning](#infrastructure-security-scanning)
      - [Multi-Environment Management](#multi-environment-management)
      - [State Analysis and Reporting](#state-analysis-and-reporting)
      - [Custom Validation and Policy Checks](#custom-validation-and-policy-checks)
  - [Error Handling](#error-handling)
  - [Configuration Options](#configuration-options)
    - [Environment Variables](#environment-variables)
    - [Binary Selection](#binary-selection)
    - [Logging and Debugging](#logging-and-debugging)
  - [API Reference](#api-reference)
    - [Tofu Class](#tofu-class)
    - [Data Models](#data-models)
  - [Requirements](#requirements)
  - [Contributing](#contributing)
  - [License](#license)


## Installation

Either `tofu` or `terraform` must be installed and available in your PATH.

```bash
pip install tofupy
```

## Quick Start

```python
from tofupy import Tofu

# Initialize a workspace
workspace = Tofu(cwd="/path/to/terraform/config")

# Initialize Terraform
workspace.init()

# Validate configuration
validation = workspace.validate()
if not validation.valid:
    print("Configuration is invalid!")
    for diagnostic in validation.diagnostics:
        print(f"Error: {diagnostic.summary}")

# Create and review a plan
plan_log, plan = workspace.plan()
if plan and not plan.errored:
    print(f"Plan will create {len([c for c in plan.resource_changes.values() if 'create' in c.change.actions])} resources")

# Apply changes
apply_log = workspace.apply()
print(f"Applied: {apply_log.added} added, {apply_log.changed} changed, {apply_log.removed} removed")

# Get outputs
outputs = workspace.output()
for name, output in outputs.items():
    print(f"{name}: {output.value} (type: {output.type})")
```

## Core Concepts

### The Tofu Class

The `Tofu` class is your main interface to Terraform/OpenTofu operations:

```python
from tofupy import Tofu

# Basic initialization
workspace = Tofu()  # Uses current directory

# Custom configuration
workspace = Tofu(
    cwd="/path/to/terraform/config",
    binary="terraform",  # or "tofu"
    log_level="DEBUG",   # ERROR, WARN, INFO, DEBUG
    env={"TF_VAR_environment": "production"}
)

# The workspace automatically detects binary version and validates compatibility
print(f"Using {workspace.binary_path} version {workspace.version} on {workspace.platform}")
```

### Structured Data Models

TofuPy provides rich Python data classes that mirror Terraform's JSON structures:

- `Plan` - Terraform plan with resource changes, drift detection, and metadata
- `State` - Current Terraform state with resources and outputs
- `ApplyLog`/`PlanLog` - Execution logs with summaries and diagnostics
- `Validate` - Validation results with error/warning details
- `Output` - Terraform outputs with values, types, and sensitivity info
- `Resource` - Individual resources with addresses, types, and values
- `Change` - Resource changes with before/after states and actions

## Detailed Usage Examples

### Infrastructure Lifecycle Management

#### Initialization

```python
from tofupy import Tofu

workspace = Tofu(cwd="./terraform")

# Basic initialization
success = workspace.init()

# Initialize with backend configuration
success = workspace.init(backend_conf="backend.hcl")

# Initialize without backend (useful for validation)
success = workspace.init(disable_backends=True)

# Initialize with extra arguments
success = workspace.init(extra_args=["-upgrade"])
```

#### Configuration Validation

```python
# Validate configuration
validation = workspace.validate()

print(f"Configuration valid: {validation.valid}")
print(f"Errors: {validation.error_count}, Warnings: {validation.warning_count}")

# Handle validation issues
if not validation.valid:
    for diagnostic in validation.diagnostics:
        if diagnostic.severity == "error":
            print(f"❌ {diagnostic.summary}")
            print(f"   {diagnostic.detail}")
        else:
            print(f"⚠️  {diagnostic.summary}")
```

#### Planning Changes

```python
# Basic plan
plan_log, plan = workspace.plan()

# Plan with variables
plan_log, plan = workspace.plan(
    variables={
        "environment": "production",
        "instance_count": "3"
    }
)

# Plan with output to file
from pathlib import Path
plan_file = Path("./my-plan.tfplan")
plan_log, plan = workspace.plan(plan_file=plan_file)

# Plan with extra arguments
plan_log, plan = workspace.plan(
    extra_args=["-target=aws_instance.example"]
)

# Analyze the plan
if plan and not plan.errored:
    print(f"Terraform version: {plan.terraform_version}")
    print(f"Plan is applyable: {plan.applyable}")

    # Review resource changes
    for address, change_container in plan.resource_changes.items():
        change = change_container.change
        actions = ", ".join(change.actions)
        print(f"{address}: {actions}")

        # Check for creates
        if "create" in change.actions:
            print(f"  Will create {change_container.type} resource")

        # Check for updates
        if "update" in change.actions:
            print(f"  Will modify {change_container.type} resource")

        # Check for destroys
        if "delete" in change.actions:
            print(f"  Will destroy {change_container.type} resource")
```

#### Applying Changes

```python
# Apply from plan file
apply_log = workspace.apply(plan_file=plan_file)

# Direct apply with variables
apply_log = workspace.apply(
    variables={"environment": "staging"}
)

# Apply with auto-approval (default)
apply_log = workspace.apply()

# Review apply results
print(f"Operation: {apply_log.operation}")
print(f"Resources: +{apply_log.added} ~{apply_log.changed} -{apply_log.removed}")

# Handle errors
if apply_log.errors:
    print("Apply encountered errors:")
    for error in apply_log.errors:
        print(f"  {error.summary}: {error.detail}")
```

#### Managing State

```python
# Get current state
state = workspace.state()

print(f"State serial: {state.serial}")
print(f"State lineage: {state.lineage}")
print(f"Terraform version: {state.terraform_version}")

# Access state outputs
for name, output in state.outputs.items():
    if output.sensitive:
        print(f"{name}: <sensitive>")
    else:
        print(f"{name}: {output.value} ({output.type})")

# Access state resources
root_module = state.root_module
if root_module:
    for address, resource in root_module.resources.items():
        print(f"Resource: {address}")
        print(f"  Type: {resource.type}")
        print(f"  Provider: {resource.provider_name}")
        print(f"  Values: {resource.values}")
```

#### Getting Outputs

```python
# Get all outputs
outputs = workspace.output()

for name, output in outputs.items():
    print(f"Output '{name}':")
    print(f"  Value: {output.value}")
    print(f"  Type: {output.type}")
    print(f"  Sensitive: {output.sensitive}")

# Work with specific outputs
if "database_url" in outputs:
    db_url = outputs["database_url"].value
    print(f"Connecting to database: {db_url}")
```

#### Destroying Infrastructure

```python
# Destroy all resources
destroy_log = workspace.destroy()

print(f"Destroyed {destroy_log.removed} resources")

# Handle destruction errors
if destroy_log.errors:
    print("Destroy encountered errors:")
    for error in destroy_log.errors:
        print(f"  {error.summary}")
```

### Event Handling and Real-time Monitoring

TofuPy allows you to hook into Terraform's execution stream for real-time monitoring:

```python
def progress_handler(event):
    """Handle progress events during plan/apply"""
    if event.get("type") == "apply_progress":
        resource = event.get("hook", {}).get("resource", {})
        action = resource.get("action")
        addr = resource.get("addr")
        print(f"Progress: {action} {addr}")
    return True

def error_handler(event):
    """Handle error events"""
    if event.get("@level") == "error":
        print(f"Error: {event.get('@message')}")
    return True

def summary_handler(event):
    """Handle change summaries"""
    if event.get("type") == "change_summary":
        changes = event.get("changes", {})
        add = changes.get("add", 0)
        change = changes.get("change", 0)
        remove = changes.get("remove", 0)
        print(f"Summary: +{add} ~{change} -{remove}")
    return True

# Use event handlers during operations
plan_log, plan = workspace.plan(
    event_handlers={
        "apply_progress": progress_handler,
        "diagnostic": error_handler,
        "change_summary": summary_handler,
        "all": lambda e: print(f"Event: {e.get('type')}")  # Catch all events
    }
)

apply_log = workspace.apply(
    event_handlers={
        "apply_progress": progress_handler,
        "change_summary": summary_handler
    }
)
```

### Advanced Use Cases

#### Infrastructure Security Scanning

```python
from tofupy import Tofu

def scan_security_groups(workspace_path):
    """Scan for overly permissive security groups"""
    workspace = Tofu(cwd=workspace_path)
    workspace.init()

    plan_log, plan = workspace.plan()
    if not plan or plan.errored:
        print("❌ Planning failed")
        return

    issues = []
    for address, change_container in plan.resource_changes.items():
        if change_container.type == "aws_security_group_rule":
            change = change_container.change

            # Check for rules allowing all traffic from internet
            if change.after and change.after.get("cidr_blocks") == ["0.0.0.0/0"]:
                if change.after.get("from_port") == 0 and change.after.get("to_port") == 65535:
                    issues.append(f"⚠️  {address} allows all traffic from internet")
                elif change.after.get("from_port") == 22:
                    issues.append(f"⚠️  {address} allows SSH from internet")

    if issues:
        print("Security issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ No security issues detected")

# Usage
scan_security_groups("./infrastructure")
```

#### Multi-Environment Management

```python
from tofupy import Tofu
from pathlib import Path

class InfrastructureManager:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.environments = {}

    def setup_environment(self, env_name, variables=None):
        """Initialize a Terraform workspace for an environment"""
        env_path = self.base_path / env_name
        workspace = Tofu(
            cwd=str(env_path),
            env={f"TF_VAR_{k}": str(v) for k, v in (variables or {}).items()}
        )

        # Initialize with environment-specific backend
        backend_config = env_path / "backend.hcl"
        if backend_config.exists():
            workspace.init(backend_conf=backend_config)
        else:
            workspace.init()

        self.environments[env_name] = workspace
        return workspace

    def deploy_all(self, environments=None):
        """Deploy to multiple environments"""
        target_envs = environments or self.environments.keys()

        for env_name in target_envs:
            print(f"\n🚀 Deploying to {env_name}...")
            workspace = self.environments[env_name]

            # Validate first
            validation = workspace.validate()
            if not validation.valid:
                print(f"❌ {env_name} configuration invalid")
                continue

            # Plan changes
            plan_log, plan = workspace.plan()
            if not plan or plan.errored:
                print(f"❌ {env_name} planning failed")
                continue

            # Show summary
            creates = len([c for c in plan.resource_changes.values()
                          if 'create' in c.change.actions])
            updates = len([c for c in plan.resource_changes.values()
                          if 'update' in c.change.actions])
            deletes = len([c for c in plan.resource_changes.values()
                          if 'delete' in c.change.actions])

            print(f"  Plan: +{creates} ~{updates} -{deletes}")

            # Apply changes
            apply_log = workspace.apply()
            if apply_log.errors:
                print(f"❌ {env_name} apply failed")
                for error in apply_log.errors:
                    print(f"    {error.summary}")
            else:
                print(f"✅ {env_name} deployed successfully")

# Usage
manager = InfrastructureManager("./environments")

# Setup environments
manager.setup_environment("dev", {"instance_type": "t3.micro"})
manager.setup_environment("staging", {"instance_type": "t3.small"})
manager.setup_environment("prod", {"instance_type": "t3.medium"})

# Deploy to all environments
manager.deploy_all()
```

#### State Analysis and Reporting

```python
def generate_infrastructure_report(workspace_path):
    """Generate a comprehensive infrastructure report"""
    workspace = Tofu(cwd=workspace_path)

    # Get current state
    state = workspace.state()

    print("=== Infrastructure Report ===\n")
    print(f"Terraform Version: {state.terraform_version}")
    print(f"State Serial: {state.serial}")
    print(f"State Lineage: {state.lineage}")

    # Analyze resources by provider
    providers = {}
    resource_types = {}

    if state.root_module:
        for address, resource in state.root_module.resources.items():
            provider = resource.provider_name or "unknown"
            providers[provider] = providers.get(provider, 0) + 1

            resource_types[resource.type] = resource_types.get(resource.type, 0) + 1

    print(f"\n=== Resources by Provider ===")
    for provider, count in sorted(providers.items()):
        print(f"  {provider}: {count} resources")

    print(f"\n=== Resources by Type ===")
    for rtype, count in sorted(resource_types.items()):
        print(f"  {rtype}: {count}")

    # List outputs
    print(f"\n=== Outputs ===")
    if state.outputs:
        for name, output in state.outputs.items():
            status = "sensitive" if output.sensitive else "public"
            print(f"  {name} ({output.type}): {status}")
    else:
        print("  No outputs defined")

# Usage
generate_infrastructure_report("./terraform")
```

#### Custom Validation and Policy Checks

```python
def validate_infrastructure_policies(workspace_path):
    """Run custom policy validations on planned infrastructure"""
    workspace = Tofu(cwd=workspace_path)
    workspace.init()

    plan_log, plan = workspace.plan()
    if not plan or plan.errored:
        print("❌ Cannot validate - planning failed")
        return False

    violations = []

    # Policy: All EC2 instances must have Name tags
    for address, change_container in plan.resource_changes.items():
        if change_container.type == "aws_instance":
            change = change_container.change
            if change.after:
                tags = change.after.get("tags", {})
                if "Name" not in tags:
                    violations.append(f"EC2 instance {address} missing Name tag")

    # Policy: No publicly accessible RDS instances
    for address, change_container in plan.resource_changes.items():
        if change_container.type == "aws_db_instance":
            change = change_container.change
            if change.after and change.after.get("publicly_accessible"):
                violations.append(f"RDS instance {address} is publicly accessible")

    # Policy: S3 buckets must have versioning enabled
    for address, change_container in plan.resource_changes.items():
        if change_container.type == "aws_s3_bucket_versioning":
            change = change_container.change
            if change.after:
                config = change.after.get("versioning_configuration", [{}])[0]
                if config.get("status") != "Enabled":
                    violations.append(f"S3 bucket versioning not enabled for {address}")

    # Report results
    if violations:
        print("❌ Policy violations found:")
        for violation in violations:
            print(f"  • {violation}")
        return False
    else:
        print("✅ All policy checks passed")
        return True

# Usage
if validate_infrastructure_policies("./terraform"):
    print("Proceeding with deployment...")
else:
    print("Fix policy violations before deploying")
```

## Error Handling

TofuPy provides comprehensive error handling through structured diagnostics:

```python
from tofupy import Tofu, Diagnostic

workspace = Tofu(cwd="./terraform")

try:
    workspace.init()

    # Validation errors
    validation = workspace.validate()
    if not validation.valid:
        print("Configuration errors:")
        for diagnostic in validation.diagnostics:
            if diagnostic.severity == "error":
                print(f"  ❌ {diagnostic.summary}")
                print(f"     {diagnostic.detail}")

    # Apply errors
    apply_log = workspace.apply()
    if apply_log.errors:
        print("Apply errors:")
        for error in apply_log.errors:
            print(f"  ❌ {error.summary}")
            if error.detail:
                print(f"     {error.detail}")

except FileNotFoundError as e:
    print(f"Terraform/OpenTofu binary not found: {e}")

except RuntimeError as e:
    print(f"Terraform operation failed: {e}")
```

## Configuration Options

### Environment Variables

TofuPy respects standard Terraform environment variables and allows custom ones:

```python
workspace = Tofu(
    env={
        "TF_VAR_region": "us-west-2",
        "TF_VAR_environment": "production",
        "AWS_PROFILE": "production",
        "TF_LOG": "DEBUG"  # Override log level
    }
)
```

### Binary Selection

```python
# Use OpenTofu
workspace = Tofu(binary="tofu")

# Use specific Terraform path
workspace = Tofu(binary="/usr/local/bin/terraform")

# Let TofuPy find the binary
workspace = Tofu()  # Tries "tofu" first, then "terraform"
```

### Logging and Debugging

```python
# Set Terraform log level
workspace = Tofu(log_level="DEBUG")  # ERROR, WARN, INFO, DEBUG

# TofuPy automatically sets TF_IN_AUTOMATION=1 for consistent output
```

## API Reference

### Tofu Class

**Constructor**: `Tofu(cwd=None, binary="tofu", log_level="ERROR", env={})`

**Methods**:

- `init(disable_backends=False, backend_conf=None, extra_args=[])` → `bool`
- `validate()` → `Validate`
- `plan(variables={}, plan_file=None, event_handlers={}, extra_args=[])` → `Tuple[PlanLog, Plan | None]`
- `apply(plan_file=None, variables={}, destroy=False, event_handlers={}, extra_args=[])` → `ApplyLog`
- `destroy()` → `ApplyLog`
- `state()` → `State`
- `output()` → `Dict[str, Output]`

### Data Models

All data models provide structured access to Terraform's JSON outputs with proper typing and nested object support. Key models include:

- **Plan**: Resource changes, drift detection, variables, and metadata
- **State**: Current infrastructure state with resources and outputs
- **ApplyLog/PlanLog**: Execution logs with summaries and diagnostics
- **Validate**: Configuration validation results
- **Output**: Terraform output values with type information
- **Resource**: Individual infrastructure resources
- **Change**: Detailed before/after states for resource modifications

## Requirements

- Python 3.10+
- OpenTofu 1.x or Terraform 1.x installed and available in PATH
- No additional Python dependencies (uses only standard library)

## Contributing

This project is part of the Terraform in Depth book but welcomes contributions. See the repository for development setup and contribution guidelines.

## License

See LICENSE file for details.
