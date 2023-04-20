from pykeadhcp import Kea

# Connect to the Kea Agent endpoint
server = Kea(host="http://[::1]", port=9099)

# Fetch the DHCP4 Kea configuration
config = server.dhcp4.config_get()

# Print a configuration value
print( "Kea DHCP setting 'authoritative':", config['arguments']['Dhcp4']['authoritative'] )

# Change a configuration value
config['arguments']['Dhcp4']['authoritative'] = True

# Sending the new configuration to Kea DHCP4
response = server.dhcp4.config_set(config["arguments"])
assert response["result"] == 0

# Write the new configuration back to the config file
response = server.dhcp4.config_write("/etc/kea/kea-dhcp4.conf")
assert response["result"] == 0

