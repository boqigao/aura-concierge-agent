variable "project_id" {
  description = "Google Cloud Project ID hosting the Aura Executive Concierge Agent"
  type        = string
  default     = "aura-concierge-prod"
}

variable "region" {
  description = "Primary Google Cloud region for Cloud Run and Vertex AI Agent Engine"
  type        = string
  default     = "us-central1"
}

variable "container_image" {
  description = "Artifact Registry container image built via agents-cli deploy"
  type        = string
  default     = "us-central1-docker.pkg.dev/aura-concierge-prod/agents/aura-concierge-agent:latest"
}
