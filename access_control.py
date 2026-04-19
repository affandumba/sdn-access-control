"""
access_control.py
===========================================
Project : SDN-Based Access Control System
Course  : Computer Networks - UE24CS252B
SRN     : PES1UG24CS280
===========================================
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
import logging

WHITELIST = {
    '00:00:00:00:00:01',   # h1 - authorized
    '00:00:00:00:00:02',   # h2 - authorized
    '00:00:00:00:00:03',   # h3 - authorized
    # h4 is NOT in whitelist = unauthorized
}

IDLE_TIMEOUT = 60
HARD_TIMEOUT = 120

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(message)s',
    handlers=[
        logging.FileHandler('access_log.txt'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('AccessControl')


class AccessControlApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(AccessControlApp, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.stats = {
            'allowed': 0,
            'blocked': 0,
            'total'  : 0,
        }
        log.info("=" * 55)
        log.info("  SDN Access Control Controller Started")
        log.info("  Whitelist has %d authorized hosts", len(WHITELIST))
        log.info("=" * 55)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto  = datapath.ofproto
        parser   = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(
            ofproto.OFPP_CONTROLLER,
            ofproto.OFPCML_NO_BUFFER
        )]
        self._install_flow(datapath, priority=0, match=match, actions=actions)
        log.info("[SWITCH] Switch %s connected. Table-miss rule installed.", datapath.id)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg      = ev.msg
        datapath = msg.datapath
        ofproto  = datapath.ofproto
        parser   = datapath.ofproto_parser
        in_port  = msg.match['in_port']
        dpid     = datapath.id

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None:
            return

        src = eth.src
        dst = eth.dst

        # ── Ignore IPv6 multicast and special control packets ──
        if (dst.startswith('33:33') or
            dst.startswith('01:80:c2') or
            dst.startswith('01:00:5e')):
            return

        self.stats['total'] += 1

        # ── MAC Learning ──────────────────────────────────────
        if dpid not in self.mac_to_port:
            self.mac_to_port[dpid] = {}
        self.mac_to_port[dpid][src] = in_port

        # ── Skip LLDP ─────────────────────────────────────────
        if eth.ethertype == 0x88cc:
            return

        # ── Access Control Decision ───────────────────────────
        src_allowed = src in WHITELIST
        dst_allowed = dst in WHITELIST or dst == 'ff:ff:ff:ff:ff:ff'

        if src_allowed and dst_allowed:
            self._handle_allowed(datapath, msg, src, dst, in_port)
        else:
            self._handle_blocked(datapath, msg, src, dst, in_port)

    def _handle_allowed(self, datapath, msg, src, dst, in_port):
        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser
        dpid    = datapath.id

        self.stats['allowed'] += 1
        log.info("[ALLOW]  %-20s --> %-20s  port=%s  switch=%s",
                 src, dst, in_port, dpid)

        if dst in self.mac_to_port.get(dpid, {}):
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(
                in_port=in_port,
                eth_src=src,
                eth_dst=dst
            )
            self._install_flow(
                datapath,
                priority=10,
                match=match,
                actions=actions,
                idle_timeout=IDLE_TIMEOUT,
                hard_timeout=HARD_TIMEOUT
            )

        self._send_packet(datapath, msg, actions)

    def _handle_blocked(self, datapath, msg, src, dst, in_port):
        parser = datapath.ofproto_parser
        dpid   = datapath.id

        self.stats['blocked'] += 1
        log.warning("[BLOCK]  %-20s --> %-20s  port=%s  switch=%s  UNAUTHORIZED",
                    src, dst, in_port, dpid)

        match = parser.OFPMatch(
            in_port=in_port,
            eth_src=src
        )
        self._install_flow(
            datapath,
            priority=20,
            match=match,
            actions=[],
            idle_timeout=IDLE_TIMEOUT,
            hard_timeout=HARD_TIMEOUT
        )

        log.info("[STATS]  Total=%d  Allowed=%d  Blocked=%d",
                 self.stats['total'],
                 self.stats['allowed'],
                 self.stats['blocked'])

    def _install_flow(self, datapath, priority, match, actions,
                      idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser

        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions,
            idle_timeout=idle_timeout,
            hard_timeout=hard_timeout
        )
        datapath.send_msg(flow_mod)

    def _send_packet(self, datapath, msg, actions):
        parser  = datapath.ofproto_parser
        in_port = msg.match['in_port']

        packet_out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data
        )
        datapath.send_msg(packet_out)
