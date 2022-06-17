import ipaddress
from socket import AF_INET, AF_INET6
from typing import List

import dbus

from pyroute2 import IPRoute

from .utils import IpAndPort


class SystemdResolvedConnector:
    def __init__(self, interface, listen_addresses: List[IpAndPort], dns_domains, handler):
        super().__init__()

        self.interface = interface
        self.listen_addresses = listen_addresses
        self.dns_domains = dns_domains
        self.handler = handler

        self.ifindex = self.resolve_ifindex(interface)

    @staticmethod
    def resolve_ifindex(interface):
        with IPRoute() as ipr:
            ifi = ipr.link_lookup(ifname=interface)
            if not ifi:
                raise ValueError("Unknown interface '%s'" % interface)

            return ifi[0]

    @staticmethod
    def if_manager():
        system_bus = dbus.SystemBus()
        proxy = system_bus.get_object('org.freedesktop.resolve1', '/org/freedesktop/resolve1')
        return dbus.Interface(proxy, 'org.freedesktop.resolve1.Manager')

    def register(self):
        self.handler.log("Registering with systemd-resolved - interface: %s, domains: %s, dns server: %s" % (
            self.interface, self.dns_domains, ", ".join(map(lambda x: str(x), self.listen_addresses))))

        domains = [[domain.strip("."), True] for domain in self.dns_domains]
        ips = [
            [
                AF_INET if isinstance(ip_port.ip, ipaddress.IPv4Address) else AF_INET6,
                ip_port.ip.packed,
                ip_port.port,
                "",
            ]
            for ip_port in self.listen_addresses
        ]

        manager = self.if_manager()
        manager.SetLinkDNSEx(self.ifindex, ips)
        manager.SetLinkDNSSEC(self.ifindex, "no")
        manager.SetLinkDomains(self.ifindex, domains)

    def unregister(self):
        self.handler.log("Unregistering with systemd-resolved: %s" % self.interface)

        manager = self.if_manager()
        manager.RevertLink(self.ifindex)
