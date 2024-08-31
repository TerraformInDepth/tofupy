# Tofu UI

The OpenTofu and Terraform projects both use the same [Machine Readable UI](https://developer.hashicorp.com/terraform/internals/machine-readable-ui) for streaming events (plan and apply). This results in one line per event, with each line being a complete JSON object.

For non-streaming events, such as the output of `tofu show`, the [JSON Output Format](https://developer.hashicorp.com/terraform/internals/json-format) is used.
