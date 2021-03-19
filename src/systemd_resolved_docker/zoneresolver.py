import copy

from dnslib import RR, QTYPE, RCODE
from dnslib.server import BaseResolver


class ZoneResolver(BaseResolver):
    """
        Simple fixed zone file resolver.
    """

    def __init__(self, zone, glob=False):
        """
            Initialise resolver from zone file.
            Stores RRs as a list of (label,type,rr) tuples
            If 'glob' is True use glob match against zone file
        """
        self.glob = glob
        self.eq = 'matchGlob' if glob else '__eq__'
        self.zone = []
        self.update(zone)

    def update(self, zone):
        self.zone = [(rr.rname, QTYPE[rr.rtype], rr) for rr in zone]

    def resolve(self, request, handler):
        """
            Respond to DNS request - parameters are request packet & handler.
            Method is expected to return DNS response
        """
        reply = request.reply()
        qname = request.q.qname
        qtype = QTYPE[request.q.qtype]

        zone = self.zone
        for name, rtype, rr in zone:
            # Check if label & type match
            if getattr(qname, self.eq)(name) and (qtype == rtype or
                                                  qtype == 'ANY' or
                                                  rtype == 'CNAME'):
                # If we have a glob match fix reply label
                if self.glob:
                    a = copy.copy(rr)
                    a.rname = qname
                    reply.add_answer(a)
                else:
                    reply.add_answer(rr)
                # Check for A/AAAA records associated with reply and
                # add in additional section
                if rtype in ['CNAME', 'NS', 'MX', 'PTR']:
                    for a_name, a_rtype, a_rr in zone:
                        if a_name == rr.rdata.label and a_rtype in ['A', 'AAAA']:
                            reply.add_ar(a_rr)

        if not reply.rr:
            reply.header.rcode = RCODE.NXDOMAIN

        return reply
