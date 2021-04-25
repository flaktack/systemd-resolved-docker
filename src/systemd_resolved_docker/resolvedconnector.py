import ipaddress
from socket import AF_INET, AF_INET6

import dbus

from pyroute2 import IPRoute


class SystemdResolvedConnector:
    def __init__(self, docker_interface, listen_addresses, dns_domains):
        super().__init__()

        self.docker_interface = docker_interface
        self.listen_addresses = listen_addresses
        self.dns_domains = dns_domains

        self.ifindex = self.resolve_ifindex(docker_interface)

    @staticmethod
    def resolve_ifindex(docker_interface):
        with IPRoute() as ipr:
            ifi = ipr.link_lookup(ifname=docker_interface)
            if not ifi:
                raise ValueError("Unknown interface '%s'" % docker_interface)

            return ifi[0]

    @staticmethod
    def if_manager():
        system_bus = dbus.SystemBus()
        proxy = system_bus.get_object('org.freedesktop.resolve1', '/org/freedesktop/resolve1')
        return dbus.Interface(proxy, 'org.freedesktop.resolve1.Manager')

    def register(self):
        domains = [[domain.strip("."), True] for domain in self.dns_domains]
        ips = [
            [
                AF_INET if isinstance(ip, ipaddress.IPv4Address) else AF_INET6,
                ip.packed
            ]
            for ip in [ipaddress.ip_address(ip) for ip in self.listen_addresses]
        ]

        manager = self.if_manager()
        manager.SetLinkDomains(self.ifindex, domains)
        manager.SetLinkDNS(self.ifindex, ips)
        manager.SetLinkDNSSEC(self.ifindex, "no")

    def unregister(self):
        manager = self.if_manager()
        manager.RevertLink(self.ifindex)
