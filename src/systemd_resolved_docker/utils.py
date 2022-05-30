def find_docker_dns_servers(cli):
    return []


def find_default_docker_bridge_gateways(cli):
    networks = cli.networks.list()

    addresses = []
    for network in networks:
        if 'Options' in network.attrs and network.attrs['Options'].get('com.docker.network.bridge.default_bridge') == 'true':
            name = network.attrs['Options']['com.docker.network.bridge.name']
        elif network.attrs.get('Driver') == 'bridge':
            name = f"br-{network.attrs['Id'][0:12]}"
        else:
            continue

        if 'IPAM' not in network.attrs:
            continue

        if 'Config' not in network.attrs['IPAM']:
            continue

        for config in network.attrs['IPAM']['Config']:
            if 'Gateway' in config:
                gateway = config['Gateway']
                print("Found gateway %s for %s" % (gateway, name))
                addresses.append({'gateway': gateway, 'interface': name})
            elif 'Subnet' in config:
                print("Found only subnet for %s" % name)
                addresses.append({'interface': name})

    return addresses
