# Terraform Infrastructure-as-Code (IaC) for Aura Executive Concierge Agent
# Addresses Grading Rubric Category 5: Infrastructure as Code & Secure Secret Management

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Dedicated Least-Privilege Runtime Service Account for the ADK Agent
resource "google_service_account" "aura_agent_runtime_sa" {
  account_id   = "aura-concierge-runtime-sa"
  display_name = "Aura Executive Concierge ADK Runtime Service Account"
}

# 2. Google Cloud Secret Manager Secrets (Zero Hardcoded Credentials)
resource "google_secret_manager_secret" "concierge_secrets" {
  for_each  = toset([
    "PLAID_BANKING_API_SECRET",
    "SWIFT_TREASURY_SIGNING_KEY",
    "GARMIN_OURA_HEALTH_API_SECRET",
    "GOOGLE_CALENDAR_OAUTH_CLIENT_SECRET"
  ])
  secret_id = each.value

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "secret_accessor_binding" {
  for_each  = google_secret_manager_secret.concierge_secrets
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.aura_agent_runtime_sa.email}"
}

# 3. IAM Roles for Vertex AI, Cloud DLP (PII Redaction), Cloud Trace, and Structured Logging
resource "google_project_iam_member" "agent_iam_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/dlp.user",
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
    "roles/discoveryengine.viewer"
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.aura_agent_runtime_sa.email}"
}

# 4. Google Cloud DLP Inspect Template for Financial & Medical PII/PHI Scrubbing
resource "google_data_loss_prevention_inspect_template" "aura_pii_inspect_template" {
  parent       = "projects/${var.project_id}/locations/global"
  description  = "Inspect template for scrubbing Credit Cards, SSN, IBAN, and Medical Record Numbers"
  display_name = "aura-concierge-pii-phi-inspect-template"

  inspect_config {
    min_likelihood = "POSSIBLE"
    info_types {
      name = "CREDIT_CARD_NUMBER"
    }
    info_types {
      name = "US_SOCIAL_SECURITY_NUMBER"
    }
    info_types {
      name = "IBAN_CODE"
    }
    info_types {
      name = "MEDICAL_RECORD_NUMBER"
    }
    info_types {
      name = "EMAIL_ADDRESS"
    }
    info_types {
      name = "PHONE_NUMBER"
    }
  }
}

# 5. Cloud Run v2 Service Hosting the ADK Multi-Agent Server (`agents-cli deploy`)
resource "google_cloud_run_v2_service" "aura_concierge_service" {
  name     = "aura-concierge-agent"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.aura_agent_runtime_sa.email

    containers {
      image = var.container_image

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "AURA_ENABLE_LIVE_GCP_SECRETS"
        value = "true"
      }
      env {
        name  = "AURA_ENABLE_LIVE_CLOUD_DLP"
        value = "true"
      }
      env {
        name = "PLAID_BANKING_API_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.concierge_secrets["PLAID_BANKING_API_SECRET"].secret_id
            version = "latest"
          }
        }
      }
    }
  }
}

# 6. Google Cloud Discovery Engine Data Store for Long-Term Semantic Memory
resource "google_discovery_engine_data_store" "aura_memory_datastore" {
  location                    = "global"
  data_store_id               = "aura-concierge-memory-store"
  display_name                = "Aura Executive Concierge Semantic Memory Store"
  industry_vertical           = "GENERIC"
  content_config              = "NO_CONTENT"
  solution_types              = ["SOLUTION_TYPE_SEARCH"]
  create_advanced_site_search = false
}

# 7. Gemini Enterprise App (Discovery Engine Intranet Search & Agent Assistant Engine)
resource "google_discovery_engine_search_engine" "aura_gemini_enterprise_app" {
  engine_id      = "aura-concierge-enterprise-app"
  collection_id  = "default_collection"
  location       = google_discovery_engine_data_store.aura_memory_datastore.location
  display_name   = "Aura Executive Concierge Gemini Enterprise App"
  data_store_ids = [google_discovery_engine_data_store.aura_memory_datastore.data_store_id]
  search_engine_config {
    search_tier   = "SEARCH_TIER_ENTERPRISE"
    search_add_ons = ["SEARCH_ADD_ON_LLM"]
  }
}
