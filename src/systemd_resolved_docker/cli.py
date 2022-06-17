#!/usr/bin/env python3

import os
import signal

import docker
from systemd import daemon

from .dockerdnsconnector import DockerDNSConnector
from .resolvedconnector import SystemdResolvedConnector
from .utils import find_default_docker_bridge_gateway, parse_ip_port, parse_listen_address


class Handler:
    def on_start(self):
        daemon.notify('READY=1')
        self.log("Started daemon")

    def on_update(self, hosts):
        if len(hosts) > 0:
            message = "Refreshed - %d items\n\t%s" % (len(hosts), '\n\t'.join(map(lambda x: str(x), hosts)))
        else:
            message = "Refreshed - no running containers"

        self.log(message)

    def on_stop(self):
        self.log("Stopped daemon")

    def log(self, message):
        print(message)


def main():
    systemd_resolved_listen_address = os.environ.get("SYSTEMD_RESOLVED_LISTEN_ADDRESS", None)
    docker_listen_address = os.environ.get("DOCKER_LISTEN_ADDRESS", None)
    dns_server = parse_ip_port(os.environ.get("UPSTREAM_DNS_SERVER", "127.0.0.53"))
    default_domain = os.environ.get("DEFAULT_DOMAIN", "docker")

    tld = os.environ.get('ALLOWED_DOMAINS', None)
    if tld is None or len(tld.strip()) == 0:
        domains = [".docker"]
    else:
        domains = [item.strip() for item in tld.split(',')]

    cli = docker.from_env()
    docker_gateway = find_default_docker_bridge_gateway(cli)

    systemd_resolved_interface = os.environ.get('DOCKER_INTERFACE', None)
    if systemd_resolved_interface is None or len(systemd_resolved_interface) < 1:
        systemd_resolved_interface = docker_gateway[0]['interface']

    handler = Handler()
    handler.log("Default domain: %s, allowed domains: %s" % (default_domain, ", ".join(domains)))

    systemd_resolved_listen_addresses = parse_listen_address(systemd_resolved_listen_address,
                                                             lambda: [parse_ip_port("127.0.0.153:53")])
    docker_listen_addresses = parse_listen_address(docker_listen_address,
                                                   lambda: [parse_ip_port(entry['gateway']) for entry in
                                                            docker_gateway])

    resolved = SystemdResolvedConnector(systemd_resolved_interface, systemd_resolved_listen_addresses, domains, handler)

    dns_connector = DockerDNSConnector(systemd_resolved_listen_addresses + docker_listen_addresses, dns_server, domains,
                                       default_domain, handler, cli)
    dns_connector.start()

    resolved.register()

    def sig_handler(signum, frame):
        handler.log("Stopping - %s" % signal.Signals(signum))
        resolved.unregister()
        dns_connector.stop()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    signal.pause()


if __name__ == '__main__':
    main()
