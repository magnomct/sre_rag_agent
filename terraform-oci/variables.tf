variable "tenancy_ocid" {
  description = "OCID da Tenancy na OCI"
  type        = string
}

variable "user_ocid" {
  description = "OCID do Usuário"
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint da chave da API"
  type        = string
}

variable "private_key_path" {
  description = "Caminho para a private key da API"
  type        = string
}

variable "region" {
  description = "Região da OCI (ex: sa-saopaulo-1)"
  type        = string
  default     = "sa-saopaulo-1"
}

variable "compartment_ocid" {
  description = "OCID do Compartment onde os recursos serão criados"
  type        = string
}

variable "project_name" {
  description = "Nome do projeto para prefixo dos recursos"
  type        = string
  default     = "sre-rag"
}

variable "kubernetes_version" {
  description = "Versão do Kubernetes suportada pelo OKE"
  type        = string
  default     = "v1.30.1" # Verifique as versões suportadas na sua região
}

variable "node_shape" {
  description = "Shape das instâncias dos Worker Nodes"
  type        = string
  default     = "VM.Standard.E4.Flex"
}
