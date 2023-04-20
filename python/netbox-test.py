from pprint import pprint
import pynetbox
nb = pynetbox.api(
    'http://netbox.dane.onl',
    token='API-Token'
)

subnets = nb.ipam.prefixes.all()
for subnet in subnets:
 pprint(dict(subnet))
