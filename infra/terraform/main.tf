terraform {
  required_version = ">= 1.5"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "perimeter-terraform-state"
    prefix = "prod"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# GCP Memorystore (Redis)
resource "google_redis_instance" "cache" {
  name           = "perimeter-cache"
  tier           = "STANDARD_HA"
  memory_size_gb = 5
  region         = var.region
  
  redis_version     = "REDIS_7_0"
  display_name      = "Perimeter Cache"
  reserved_ip_range = "10.0.0.0/29"
  
  authorized_network = google_compute_network.vpc.id
  
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 2
        minutes = 0
      }
    }
  }
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "perimeter-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "perimeter-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}

# Cloud Run Service
resource "google_cloud_run_service" "gateway" {
  name     = "perimeter-gateway"
  location = var.region
  
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/perimeter-gateway:latest"
        
        env {
          name  = "ENVIRONMENT"
          value = "production"
        }
        
        env {
          name  = "REDIS_URL"
          value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}"
        }
        
        resources {
          limits = {
            cpu    = "2000m"
            memory = "2Gi"
          }
        }
      }
      
      container_concurrency = 80
      timeout_seconds      = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "3"
        "autoscaling.knative.dev/maxScale" = "100"
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.connector.name
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# VPC Access Connector
resource "google_vpc_access_connector" "connector" {
  name          = "perimeter-connector"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
}

# Cloud Run IAM
resource "google_cloud_run_service_iam_member" "public" {
  service  = google_cloud_run_service.gateway.name
  location = google_cloud_run_service.gateway.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud SQL (PostgreSQL)
resource "google_sql_database_instance" "main" {
  name             = "perimeter-db"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier              = "db-g1-small"
    availability_type = "REGIONAL"
    disk_size         = 20
    disk_type         = "PD_SSD"
    
    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      point_in_time_recovery_enabled = true
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }
  
  deletion_protection = true
}

resource "google_sql_database" "database" {
  name     = "perimeter"
  instance = google_sql_database_instance.main.name
}

# Outputs
output "gateway_url" {
  value = google_cloud_run_service.gateway.status[0].url
}

output "redis_host" {
  value = google_redis_instance.cache.host
}

output "db_connection_name" {
  value = google_sql_database_instance.main.connection_name
}
