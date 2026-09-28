# ------------------------------------------------------------------
# OKE Cluster (Control Plane)
# ------------------------------------------------------------------
resource "oci_containerengine_cluster" "oke_cluster" {
  compartment_id     = var.compartment_ocid
  kubernetes_version = var.kubernetes_version
  name               = "${var.project_name}-oke"
  vcn_id             = oci_core_vcn.sre_vcn.id

  endpoint_config {
    is_public_ip_enabled = true
    subnet_id            = oci_core_subnet.public_lb_subnet.id
  }

  options {
    add_ons {
      is_kubernetes_dashboard_enabled = false
      is_tiller_enabled               = false
    }
    kubernetes_network_config {
      pods_cidr     = "10.244.0.0/16"
      services_cidr = "10.96.0.0/16"
    }
  }
}

# ------------------------------------------------------------------
# Consulta do Image ID otimizado para o OKE na região
# ------------------------------------------------------------------
data "oci_core_images" "oke_images" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.node_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# ------------------------------------------------------------------
# OKE Node Pool (Worker Nodes)
# ------------------------------------------------------------------
resource "oci_containerengine_node_pool" "oke_node_pool" {
  cluster_id         = oci_containerengine_cluster.oke_cluster.id
  compartment_id     = var.compartment_ocid
  kubernetes_version = var.kubernetes_version
  name               = "${var.project_name}-np"
  
  node_shape = var.node_shape

  node_shape_config {
    memory_in_gbs = 16
    ocpus         = 2
  }

  node_source_details {
    image_id    = data.oci_core_images.oke_images.images[0].id
    source_type = "IMAGE"
  }

  node_config_details {
    placement_configs {
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
      subnet_id           = oci_core_subnet.private_node_subnet.id
    }
    placement_configs {
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[1].name
      subnet_id           = oci_core_subnet.private_node_subnet.id
    }
    size = 3 # Total de nós no pool (Scaling fixo inicial)
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}
