provider "google" {
  credentials = "${file("credentials.json")}"
  project     = var.project_name
  region      = var.region
  zone        = var.zone
}

variable "project_name" {
  type = string
  description = "The GCP project to which these settings relate"
}
variable "region" {
  type = string
  description = "The GCP region"
}
variable "zone" {
  type = string
  description = "The GCP zone"
}

variable service_name {
  type = string
  description = "The given name of the service. "
}

variable docker_image_location {
  type = string
  description = "The artefact registry location for the code."
}

variable SECRET_REF {
  type = string
  description = "The resource link to Google Secret Manager"
}

resource "google_cloud_run_service" "default" {
  name      = var.service_name
  location  = var.zone
  project   = var.project_name

  template {
    spec {
      containers {
        image = var.docker_image_location
          env {
            name = "IMAGE_DETAILS"
            value = var.docker_image_location
          }
          env {
            name = "SECRET_REF"
            value = var.SECRET_REF
          }
          startup_probe {
              initial_delay_seconds = 0
              timeout_seconds = 1
              period_seconds = 3
              failure_threshold = 1
              tcp_socket {
                port = 8080
              }
            }
            liveness_probe {
              http_get {
                path = "/health-check"
                port = 8080
              }
            }
        }
    }
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.default.location
  project     = google_cloud_run_service.default.project
  service     = google_cloud_run_service.default.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
