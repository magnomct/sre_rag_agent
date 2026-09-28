output "cluster_id" {
  description = "OCID do Cluster OKE"
  value       = oci_containerengine_cluster.oke_cluster.id
}

output "kubeconfig_command" {
  description = "Comando OCI CLI para gerar o kubeconfig e conectar ao cluster"
  value       = "oci ce cluster create-kubeconfig --cluster-id ${oci_containerengine_cluster.oke_cluster.id} --file $HOME/.kube/config --region ${var.region} --token-version 2.0.0  --kube-endpoint PUBLIC_ENDPOINT"
}

output "vcn_id" {
  description = "OCID da VCN"
  value       = oci_core_vcn.sre_vcn.id
}
