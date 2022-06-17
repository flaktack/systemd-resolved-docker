import ipaddress
import urllib.parse
from typing import List


class IpAndPort:
    ip: ipaddress.ip_address
    port: int

    def __init__(self, ip: ipaddress.ip_address, port: int):
        self.ip = ip
        self.port = port

    def __str__(self):
        return "%s:%s" % (self.ip.compressed, self.port)


def parse_ip_port(entry, default_port=53) -> IpAndPort:
    result = urllib.parse.urlsplit('//' + entry)
    return IpAndPort(ip=ipaddress.ip_address(result.hostname), port=result.port or default_port)


def parse_listen_address(listen_addresses, default_value) -> List[IpAndPort]:
    if listen_addresses is not None and len(listen_addresses) > 1:
        return [parse_ip_port(item) for item in listen_addresses.split(",")]
    else:
        return default_value()


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
