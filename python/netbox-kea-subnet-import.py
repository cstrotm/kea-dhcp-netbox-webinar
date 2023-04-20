# Demo code integrating NetBox and Kea DHCP
# Created for the ISC Kea DHCP Webinar on 2023-04-20
# (c) Carsten Strotmann, sys4
# Apache 2 License
# THIS IS NOT PRODUCTION CODE! IT IS AN EXAMPLE TO BUILD UPON

from datetime import datetime
from pykeadhcp import Kea
import pynetbox

# Connect to NetBox
nb = pynetbox.api(
    'http://netbox.dane.onl',
    token='API-Token'
)

# Connect to the Kea Agent endpoint
server = Kea(host="http://[::1]", port=9099)
kea_config = server.dhcp4.config_get()

# remove existing kea subnet configuration
del (kea_config['arguments']['Dhcp4']["subnet4"])

# Array of Kea Subnets
kea_subnets = []

# Fetch all subnets from NetBox
subnets = nb.ipam.prefixes.all()

# Fetch all ip-addresses from NetBox
ip_addresses = nb.ipam.ip_addresses.all()

# Iterate over all subnet from NetBox
for subnet in subnets:
 subnet_name  = subnet["prefix"]
 dhcp_options = subnet["custom_fields"]["dhcp_option"]
 dhcp_pool    = subnet["custom_fields"]["dhcp_pool"]
 # Create new Array of Subnets for Kea
 kea_subnet = {}
 print("Adding Subnet:", subnet_name)
 kea_subnet["subnet"] = subnet_name

 # If the custom fiels "dhcp_pool" is filled
 if dhcp_pool != None:
  print("  with DHCP Pool:", dhcp_pool)
  subnet_pools = []

  # Append a new Kea DHCP Pool structure
  pool = {}
  pool["pool"] = dhcp_pool

  # Append the new Pool to the Pools-Array
  subnet_pools.append(pool)

  # Add the Pools Array to the Kea Subnet config
  kea_subnet["pools"] = subnet_pools

 # Add the DHCP options
 if dhcp_options != None:
  # Remove linebreaks
  dhcp_options = ' '.join(dhcp_options.splitlines())
  # Split options into array
  options = dhcp_options.split(";")
  kea_options = []
  for option in options:
    kea_option = {}
    option = option.strip()
    if len(option) > 1:
     always_send = (option[0] == "!")
     if always_send:
      option = option[1:]
     print("  with DHCP Option:", option)
     option = option.split(":")
     kea_option["name"] = option[0]
     kea_option["data"] = option[1]
     kea_option["always-send"] = always_send

     # Add new Kea-Option to the options array
     kea_options.append(kea_option)

  # Add the Options Array to the Kea Subnet config
  kea_subnet["option-data"] = kea_options

 # Add new subnet to Array of Subnets
 kea_subnets.append(kea_subnet)

# Add the Subnets to the Kea configuration
kea_config['arguments']['Dhcp4']["subnet4"] = kea_subnets

# remove existing kea (global) reservations from the configuration
if 'reservations' in kea_config['arguments']['Dhcp4']:
 del (kea_config['arguments']['Dhcp4']['reservations'])

# Array of Kea DHCP reservations
kea_reservations = []

# Iterating over all IP-Addresses
for ip_address in ip_addresses:
 address      = ip_address["address"]
 # remove prefix notation from ip-address
 if "/" in address:
  address = address.split("/")[0]

 print("Adding reservation: ", address)

 hw_address   = ip_address["custom_fields"]["hw_address"]
 if hw_address != None:
   dhcp_options = ip_address["custom_fields"]["dhcp_option"]
   hostname     = ip_address["dns_name"]

   reservation = { "hw-address": hw_address, "hostname": hostname, "ip-address": address }
   # Add the DHCP options
   if dhcp_options != None:
    # Remove linebreaks
    dhcp_options = ' '.join(dhcp_options.splitlines())
    # Split options into array
    options = dhcp_options.split(";")
    kea_options = []
    for option in options:
      kea_option = {}
      option = option.strip()
      if len(option) > 1:
       always_send = (option[0] == "!")
       if always_send:
        option = option[1:]
       print("  with DHCP Option:", option)
       option = option.split(":")
       kea_option["name"] = option[0]
       kea_option["data"] = option[1]
       kea_option["always-send"] = always_send

       # Add new Kea-Option to the options array
       kea_options.append(kea_option)

    # Add the Options Array to the Kea reservation config
    reservation["option-data"] = kea_options

   # add new reservation to configuration
   kea_reservations.append(reservation)

# Add the reservations to the Kea configuration
kea_config['arguments']['Dhcp4']['reservations'] = kea_reservations

# Sending the new configuration to Kea DHCP4
response = server.dhcp4.config_set(kea_config["arguments"])
assert response["result"] == 0

# Write the new configuration back to the config file
response = server.dhcp4.config_write("/etc/kea/kea-dhcp4.conf")
assert response["result"] == 0

# Read current leases from Kea DHCP
print("Updating lease information from Kea DHCP into NetBox")
kea_leases = server.dhcp4.lease4_get_all([1])
kea_leases = kea_leases["arguments"]["leases"]
for lease in kea_leases:
 leasetime = lease["cltt"]
 lease_cltt = datetime.utcfromtimestamp(leasetime).strftime('%Y-%m-%d %H:%M:%S')
 print("  Lease for " + lease["ip-address"] +": valid until "+ lease_cltt + " UTC")
 try:
   nb_ip_address = nb.ipam.ip_addresses.get(address=lease["ip-address"])
   if nb_ip_address == None:
    nb_ip_address.address = nb.ipam.ip_addresses.create(
        address=lease["ip-address"],
        description="Added from Kea DHCP"
    )
    nb_ip_address.custom_fields["dhcp_lease"]=lease_cltt
    nb_ip_address.save()
   else:
    nb_ip_address.address=lease["ip-address"]
    nb_ip_address.custom_fields["dhcp_lease"]=lease_cltt
    nb_ip_address.save()

 except pynetbox.lib.query.RequestError as e:
  print(e.error)
