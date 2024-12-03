variable "state_bucket" {
  type = string
  description = "The name of the bucket holding the Terraform state"
}
variable service_name {
  type = string
  description = "The given name of the service. "
}

terraform {
 backend "gcs" {
   bucket  = var.state_bucket
   prefix  = "${ var.service_name }/terraform/state"
 }
}