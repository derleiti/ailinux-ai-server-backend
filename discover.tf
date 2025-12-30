provider "nebius" {}

data "nebius_compute_v1_instance" "existing" {
  id = "computeinstance-e01ajhk7c49kb0g4v5"
}

output "boot_disk_id" {
  value = data.nebius_compute_v1_instance.existing.boot_disk[0].existing_disk[0].id
}
