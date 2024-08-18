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



resource "google_cloud_run_v2_service" "default" {
  name      = var.service_name
  location  = var.zone
  project   = var.project_name
  ingress   = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
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
        env {
          name = "GOOGLE_APPLICATION_CREDENTIALS"
          value = "credentials.json"
        }
        startup_probe {
            initial_delay_seconds = 5
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
      vpc_access {
        network_interfaces {
          network = google_compute_network.project_network.name
          subnetwork = google_compute_subnetwork.cloudsql_subnet.name
        }
      }
  }
}

resource "google_cloud_run_service_iam_binding" "default" {
  location = google_cloud_run_v2_service.default.location
  service  = google_cloud_run_v2_service.default.name
  role     = "roles/run.invoker"
  members = [
    "allUsers"
  ]
}

#
#
#   SQL Configuration




#
#
#   VPC Configuration

# Create the basic VPC for the App. 
resource "google_compute_network" "project_network" {
  name                    = "${var.service_name}-network"
  auto_create_subnetworks = false
}

# Add a subnet for our Cloud SQL instance
resource "google_compute_subnetwork" "cloudsql_subnet" {
  name          = "${var.service_name}-sql-subnetwork"
  ip_cidr_range = "10.2.0.0/24"
  region        = var.region
  network       = google_compute_network.project_network.id
}

#
#
#   Certification Configuration

resource "google_certificate_manager_dns_authorization" "instance" {
  name        = "binaryrage-com-dns-auth"
  description = "Default"
  domain      = "archibot.binaryrage.com"
}