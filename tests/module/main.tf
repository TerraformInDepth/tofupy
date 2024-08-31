variable "website" {
  type        = string
  description = "The url to pull data from."
  default     = "https://catfact.ninja/fact"
}

data "http" "site" {
  url = var.website

  request_headers = {
    Accept = "application/json"
  }
}

resource "terraform_data" "main" {
  input = data.http.site.response_body
}

check "example" {
  assert {
    condition     = length(terraform_data.main.output) > 0
    error_message = "HTTP lookup has content."
  }

  assert {
    condition     = data.http.site.status_code >= 200 && data.http.site.status_code < 300
    error_message = "HTTP lookup returned a success status code."
  }
}

output "site_data" {
  value = terraform_data.main.output
}
