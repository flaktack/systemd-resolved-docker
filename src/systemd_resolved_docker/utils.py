def find_docker_dns_servers(cli):
    return []


def get_interface_name(docker_network):
    if 'Options' in docker_network.attrs and docker_network.attrs['Options'].get('com.docker.network.bridge.default_bridge') == 'true':
        name = docker_network.attrs['Options']['com.docker.network.bridge.name']
    elif docker_network.attrs.get('Driver') == 'bridge':
        name = f"br-{docker_network.attrs['Id'][0:12]}"
    else:
        name = None

    return name


def find_default_docker_bridge_gateways(cli):
    networks = cli.networks.list()

    addresses = []
    for network in networks:
        name = get_interface_name(network)

        if not name:
            continue

        if 'IPAM' not in network.attrs:
            continue

        if 'Config' not in network.attrs['IPAM']:
            continue

        for config in network.attrs['IPAM']['Config']:
            if 'Gateway' in config:
                gateway = config['Gateway']
                print("Found gateway %s for %s, id: %s" % (gateway, name, network.attrs['Id']))
                addresses.append({'gateway': gateway, 'interface': name, 'id': network.attrs['Id']})
            elif 'Subnet' in config:
                print("Found only subnet for %s, id: %s" % (name, network.attrs['Id']))
                addresses.append({'interface': name, 'id': network.attrs['Id']})

    return addresses
