def find_docker_dns_servers(cli):
    return []


def find_default_docker_bridge_gateway(cli):
    networks = cli.networks.list()

    addresses = []
    for network in networks:
        if 'Options' not in network.attrs:
            continue

        if 'com.docker.network.bridge.default_bridge' not in network.attrs['Options']:
            continue

        if network.attrs['Options']['com.docker.network.bridge.default_bridge'] != 'true':
            continue

        name = network.attrs['Options']['com.docker.network.bridge.name']

        if 'IPAM' not in network.attrs:
            continue

        if 'Config' not in network.attrs['IPAM']:
            continue

        for config in network.attrs['IPAM']['Config']:
            if 'Gateway' in config:
                gateway = config['Gateway']
                print("Found gateway %s for %s" % (gateway, name))
                addresses.append({'gateway': gateway, 'interface': name})

    return addresses
