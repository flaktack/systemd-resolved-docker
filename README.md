# systemd-resolved-docker

Provides systemd-resolved and docker DNS integration.

A DNS server is configured to listen on each docker interface's IP address. This is used to:
 1. expose the systemd-resolved DNS service (`127.0.0.53`) to docker containers by proxying DNS requests, since the
    systems loopback IPs can't be accessed from containers.
 2. adds the created DNS servers to the docker interface using systemd-resolved so that docker containers may
    be referenced by hostname. This uses `--hostname` and `--domainname`, `--network` or a default of `.docker` to
    create the domains.

## Install

### Fedora / COPR

For Fedora and RPM based systems [COPR](https://copr.fedorainfracloud.org/coprs/flaktack/systemd-resolved-docker/) contains pre-built packages.

1. Enabled the COPR repository
   
       dnf copr enable flaktack/systemd-resolved-docker

1.  Install the package
    
        dnf install systemd-resolved-docker
    
1. Start and optionally enable the services
   
       systemctl start  systemd-resolved-docker
       systemctl enable systemd-resolved-docker

1. Docker should be updated to use the DNS server provided by `systemd-docker-resolved.` This may be done
   globally by editing the docker daemon's configuration (`daemon.json`) or per-container using the `--dns`
   flag.

    ```js
    "dns": [
      "172.17.0.1" // docker0 interface's IP address
    ]
    ```

### Configuration

`systemd-resolved-docker` may be configured using environment variables. When installed using the RPM
`/etc/sysconfig/systemd-resolved-docker` may also be modified to update the environment variables.

| Name             | Description                                                                | Default Value                                          | Example                  |
|------------------|----------------------------------------------------------------------------|--------------------------------------------------------|--------------------------|
| DNS_SERVER       | DNS server to use when resolving queries from docker containers.           | `127.0.0.53` - systemd-resolved DNS server             | `127.0.0.53`             |
| DOCKER_INTERFACE | Docker interface name                                                      | The first docker network's interface                   | `docker0`                |
| LISTEN_ADDRESS   | IPs to listen on for queries from systemd-resolved and docker containers.  | _ip of the default docker bridge_, often `172.17.0.1`  | `172.17.0.1,127.0.0.153` |
| LISTEN_PORT      | Port to listen on for queries from systemd-resolved and docker containers. | `53`                                                   | `1053`                   |
| DEFAULT_DOMAIN   | Domain to append to containers which don't have one set using `--domainname` or are not part of a network `--network`. | `.docker`  | `.docker`                |
| ALLOWED_DOMAINS  | Domain globs which will be handled by the DNS server.                      | `.docker`                                              | `.docker,local`         |


## Usage

Start a container with a specified hostname:
`docker run --hostname test python:3.9 python -m http.server 3000`

If configured correctly then `resolvectl status` should show the configured link-specific DNS server, while the url
should load: http://test.docker:3000/

    $ resolvectl status
    ...
    Link 7 (docker0)
    Current Scopes: DNS LLMNR/IPv4 LLMNR/IPv6                                   
         Protocols: -DefaultRoute +LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
       DNS Servers: 172.17.0.1                                                  
        DNS Domain: ~docker       
    ... 

If docker is configured to use the provided DNS server then the container domain names may also be resolved within containers:

    $ docker run --dns 1.1.1.1 --rm -it alpine
    / # apk add bind
    / # host test.docker
    Host test.docker not found: 3(NXDOMAIN)

```
$ docker run --dns 172.17.0.1 --rm -it alpine
/ # apk add bind
/ # host test.docker
/ # host test.docker
test.docker has address 172.17.0.3
Host test.docker not found: 3(NXDOMAIN)
Host test.docker not found: 3(NXDOMAIN)
```

If there are link-local, VPN or other DNS servers configured than those will also work within containers.

## Build

`setup.py` may be used to create a python package.

`tito` may be used to create RPMs.


## Links

Portions are based on [docker-auto-dnsmasq](https://github.com/metal3d/docker-auto-dnsmasq).