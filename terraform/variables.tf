variable "project_id"   { type = string }
variable "region"       { type = string }
variable "bq_location"  { type = string }

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "composer_image_version" {
  description = "Composer environment for airflow"
  type        = string
}
