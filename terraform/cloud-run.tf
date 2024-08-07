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

variable sql_root_password {
  type = string
  description = "The root password for MySQL"
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

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"      = "1000"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.instance.connection_name
        "run.googleapis.com/client-name"        = "terraform"
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


resource "google_sql_database_instance" "instance" {
  name             = var.service_name
  region           = var.region
  database_version = "MYSQL_5_7"
  root_password = var.sql_root_password

  settings {
    tier = "db-f1-micro"
    
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.private_network.self_link
      enable_private_path_for_google_cloud_services = true
    }
    
  }

  deletion_protection  = "true"

}

resource "google_compute_network" "private_network" {

  name = "${var.service_name}-network"
  
}

resource "google_compute_global_address" "private_ip_address" {

  name          = "sql-private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.private_network.id

}

resource "google_service_networking_connection" "private_vpc_connection" {

  network                 = google_compute_network.private_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

resource "random_id" "db_name_suffix" {
  byte_length = 4
}