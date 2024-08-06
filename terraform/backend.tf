
terraform {
 backend "gcs" {
   bucket  = "1764315b3a30f266-bucket-tfstate"
   prefix  = "terraform/state"
 }
}