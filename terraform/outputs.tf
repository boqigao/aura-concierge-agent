output "cloud_run_service_uri" {
  description = "Public HTTPS endpoint of the deployed Aura Concierge ADK Service"
  value       = google_cloud_run_v2_service.aura_concierge_service.uri
}

output "runtime_service_account_email" {
  description = "Least-privilege service account bound to Secret Manager and Cloud DLP"
  value       = google_service_account.aura_agent_runtime_sa.email
}

output "dlp_inspect_template_id" {
  description = "Resource ID of the Cloud DLP PII/PHI inspect template"
  value       = google_data_loss_prevention_inspect_template.aura_pii_inspect_template.id
}
