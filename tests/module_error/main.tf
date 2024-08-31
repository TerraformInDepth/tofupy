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
  count = 5
  input = data.http.site.response_body
}


output "site_data" {
  value = terraform_data.main.output
}
