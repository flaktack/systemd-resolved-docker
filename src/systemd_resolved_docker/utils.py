import ipaddress
import urllib.parse
from pyroute2 import NDB
from typing import List, Union


class IpAndPort:
    def __init__(self, ip: Union[ipaddress.IPv4Address, ipaddress.IPv6Address], port: int):
        self.ip = ip
        self.port = port

    def __str__(self):
        if isinstance(self.ip, ipaddress.IPv4Address):
            return "%s:%s" % (self.ip.compressed, self.port)
        else:
            return "[%s]:%s" % (self.ip.compressed, self.port)


def parse_ip(entry, default_port=53) -> IpAndPort:
    return IpAndPort(ip=ipaddress.ip_address(entry), port=default_port)


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


def create_dummy_interface(interface, ip_addresses):
    with NDB(log='on') as ndb:
        nbd_if = ndb.interfaces.create(ifname=interface, kind="dummy")
        for ip_address in ip_addresses:
            nbd_if = nbd_if.add_ip("%s/%s" % (
                ip_address.ip.exploded, "32" if isinstance(ip_address.ip, ipaddress.IPv4Address) else "128"))

        nbd_if.set('state', 'up')
        nbd_if.commit()


def remove_dummy_interface(interface):
    with NDB(log='on') as ndb:
        ndbif = ndb.interfaces.get(interface)
        if ndbif is not None:
            ndbif.remove().commit()


def sanify_domain(domain: str):
    domain = domain.strip()
    if domain[0] == '.':
        return domain
    else:
        return '.' + domain
