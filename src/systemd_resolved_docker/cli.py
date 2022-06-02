#!/usr/bin/sudo python

# #/usr/bin/env python3

import os
import docker
import signal
from systemd import daemon

from systemd_resolved_docker.dockerwatcher import DockerWatcher
from systemd_resolved_docker.resolvedconnector import SystemdResolvedConnector
from systemd_resolved_docker.dockerdnsconnector import DockerDNSConnector

class Handler:
    def on_start(self):
        daemon.notify('READY=1')
        self.log("Started daemon")

    def on_update(self, hosts):
        message = "Refreshed - %d items (%s)" % (
            len(hosts), ' '.join(["%s/%s" % (host.ip, ','.join(host.host_names)) for host in hosts]))

        self.log(message)

    def on_stop(self):
        self.log("Stopped daemon")

    def log(self, message):
        print(message)


def main():

    dns_server = os.environ.get("DNS_SERVER", "127.0.0.53")
    default_domain = os.environ.get("DEFAULT_DOMAIN", "docker")
    listen_port = int(os.environ.get("LISTEN_PORT", "53"))
    listen_address = os.environ.get("LISTEN_ADDRESS", None)

    tld = os.environ.get('ALLOWED_DOMAINS', None)
    if tld is None or len(tld.strip()) == 0:
        domains = [".docker"]
    else:
        domains = [item.strip() for item in tld.split(',')]

    cli = docker.from_env()

    listen_addresses = None

    if listen_address is not None and len(listen_address) > 0:
        listen_addresses = listen_address.split(",")

    interface = os.environ.get('DOCKER_INTERFACE', None)

    handler = Handler()
    handler.log("Default domain: %s, allowed domains: %s" % (default_domain, ", ".join(domains)))

    systemd_resolver = SystemdResolvedConnector(interface, listen_addresses, domains, cli)

    dns_connector = DockerDNSConnector(None, listen_port, dns_server, domains, default_domain, handler, cli)

    docker_watcher = DockerWatcher(dns_connector, systemd_resolver, cli)
    docker_watcher.start()

    def sig_handler(signum, frame):
        handler.log("Stopping - %s" % signal.Signals(signum))
        systemd_resolver.stop()
        dns_connector.stop()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    signal.pause()


if __name__ == '__main__':
    main()
