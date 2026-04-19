"""
topology.py
===========================================
Project : SDN-Based Access Control System
Course  : Computer Networks - UE24CS252B
SRN     : PES1UG24CS280
===========================================

Topology:
    4 hosts connected to 1 OpenFlow switch
    Controller runs separately (Ryu)

         h1(auth)   h2(auth)   h3(auth)   h4(UNAUTH)
            |          |          |           |
            +----------+----------+-----------+
                            |
                           s1  (OpenFlow Switch)
                            |
                        Controller (Ryu)

Run order:
    Terminal 1: ryu-manager access_control.py
    Terminal 2: sudo python3 topology.py
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class AccessControlTopo(Topo):
    """
    Single switch topology with 4 hosts.
    h1, h2, h3 = authorized (in whitelist)
    h4         = unauthorized (NOT in whitelist)
    """
    def build(self):
        # Add one switch
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')

        # Add 4 hosts
        # Mininet by default assigns MACs as 00:00:00:00:00:0X
        h1 = self.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/24')
        h2 = self.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/24')
        h3 = self.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3/24')
        h4 = self.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.0.4/24')

        # Connect all hosts to the switch with 10Mbps links
        self.addLink(h1, s1, bw=10, delay='2ms')
        self.addLink(h2, s1, bw=10, delay='2ms')
        self.addLink(h3, s1, bw=10, delay='2ms')
        self.addLink(h4, s1, bw=10, delay='2ms')


def run():
    topo = AccessControlTopo()

    net = Mininet(
        topo=topo,
        controller=None,   # We connect manually below
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=False  # We set MACs manually above
    )

    # Connect to Ryu controller running on localhost port 6633
    net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6633
    )

    net.start()

    info('\n')
    info('=' * 50 + '\n')
    info('  SDN Access Control - Network Started\n')
    info('=' * 50 + '\n')
    info('  Authorized hosts   : h1, h2, h3\n')
    info('  Unauthorized host  : h4\n')
    info('\n')
    info('  Quick Tests to try:\n')
    info('  h1 ping h2        -> should SUCCEED\n')
    info('  h1 ping h3        -> should SUCCEED\n')
    info('  h4 ping h1        -> should FAIL (blocked)\n')
    info('  h4 ping h2        -> should FAIL (blocked)\n')
    info('=' * 50 + '\n\n')

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
