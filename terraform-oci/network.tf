# ------------------------------------------------------------------
# VCN (Virtual Cloud Network)
# ------------------------------------------------------------------
resource "oci_core_vcn" "sre_vcn" {
  compartment_id = var.compartment_ocid
  cidr_block     = "10.0.0.0/16"
  display_name   = "${var.project_name}-vcn"
  dns_label      = "srevcn"
}

# ------------------------------------------------------------------
# Gateways
# ------------------------------------------------------------------
resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.sre_vcn.id
  display_name   = "${var.project_name}-igw"
}

resource "oci_core_nat_gateway" "nat_gw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.sre_vcn.id
  display_name   = "${var.project_name}-nat-gw"
}

resource "oci_core_service_gateway" "sgw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.sre_vcn.id
  services {
    service_id = data.oci_core_services.all_services.services[0].id
  }
  display_name   = "${var.project_name}-sgw"
}

data "oci_core_services" "all_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

# ------------------------------------------------------------------
# Route Tables
# ------------------------------------------------------------------
resource "oci_core_route_table" "public_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.sre_vcn.id
  display_name   = "${var.project_name}-public-rt"

  route_rules {
    network_entity_id = oci_core_internet_gateway.igw.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

resource "oci_core_route_table" "private_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.sre_vcn.id
  display_name   = "${var.project_name}-private-rt"

  route_rules {
    network_entity_id = oci_core_nat_gateway.nat_gw.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
  route_rules {
    network_entity_id = oci_core_service_gateway.sgw.id
    destination       = data.oci_core_services.all_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
  }
}

# ------------------------------------------------------------------
# Subnets
# ------------------------------------------------------------------
# Subnet Pública para Load Balancers / Ingress
resource "oci_core_subnet" "public_lb_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.sre_vcn.id
  cidr_block                 = "10.0.1.0/24"
  display_name               = "${var.project_name}-public-subnet"
  route_table_id             = oci_core_route_table.public_rt.id
  prohibit_public_ip_on_vnic = false
  dns_label                  = "public"
}

# Subnet Privada para os Worker Nodes
resource "oci_core_subnet" "private_node_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.sre_vcn.id
  cidr_block                 = "10.0.2.0/24"
  display_name               = "${var.project_name}-private-nodes"
  route_table_id             = oci_core_route_table.private_rt.id
  prohibit_public_ip_on_vnic = true
  dns_label                  = "private"
}
