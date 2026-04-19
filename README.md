# SDN-Based Access Control System

**Course:** Computer Networks - UE24CS252B  
**SRN:** PES1UG24CS280  
**Project:** 11 — SDN-Based Access Control System  
**Controller:** Ryu (OpenFlow 1.3)  
**Emulator:** Mininet  

---

## Problem Statement

Design and implement an SDN-based Access Control System where only **authorized (whitelisted) hosts** are permitted to communicate on the network. Unauthorized hosts are detected at the controller and blocked via explicit DROP flow rules installed in the OpenFlow switch.

---

## Network Topology

```
  h1 (authorized)    h2 (authorized)    h3 (authorized)    h4 (UNAUTHORIZED)
  10.0.0.1           10.0.0.2           10.0.0.3           10.0.0.4
  MAC: 00:00:00:00:00:01  ...02  ...03       ...04
       |                  |                  |                  |
       +------------------+------------------+------------------+
                                    |
                             s1 (OVS Switch)
                             OpenFlow 1.3
                                    |
                          Ryu Controller (port 6633)
```

- **Authorized hosts:** h1, h2, h3 (in whitelist)
- **Unauthorized host:** h4 (NOT in whitelist — all traffic blocked)

---

## How It Works

### Controller Logic Flow

```
Packet arrives at switch
        |
        v
No matching flow rule → packet_in sent to controller
        |
        v
Controller checks src MAC and dst MAC against WHITELIST
        |
   +----|----+
   |         |
 BOTH      EITHER
 in list   not in list
   |         |
   v         v
ALLOW      BLOCK
Install    Install
forward    DROP rule
rule       (priority 20)
(priority  No packet
    10)    forwarded
Forward
packet
```

### Flow Rule Priorities

| Rule Type    | Priority | Action         | Installed When            |
|-------------|----------|----------------|---------------------------|
| Table-miss  | 0        | Send to controller | Switch connects        |
| Allow rule  | 10       | Forward to port | Authorized traffic seen  |
| Drop rule   | 20       | DROP (no action)| Unauthorized src seen    |

Higher priority = matched first. DROP rules (20) override allow rules (10).

---

## Setup Instructions

### Prerequisites

```bash
# Install Mininet
sudo apt update
sudo apt install mininet -y

# Install Ryu controller
pip install ryu

# Install Open vSwitch (if not present)
sudo apt install openvswitch-switch -y
```

### Running the Project

**Step 1 — Start Ryu Controller (Terminal 1)**
```bash
ryu-manager access_control.py
```
You should see:
```
SDN Access Control Controller Started
Whitelist has 3 authorized hosts
```

**Step 2 — Start Mininet Topology (Terminal 2)**
```bash
sudo python3 topology.py
```
You should see the Mininet CLI prompt:
```
mininet>
```

---

## Test Scenarios

### Scenario 1: Authorized Communication (should SUCCEED)

```bash
# Inside Mininet CLI:
mininet> h1 ping -c 4 h2
```
**Expected Output:**
```
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=X ms
...
4 packets transmitted, 4 received, 0% packet loss
```

```bash
mininet> h2 ping -c 4 h3
# Expected: 0% packet loss

mininet> h1 ping -c 4 h3
# Expected: 0% packet loss
```

**iperf bandwidth test between authorized hosts:**
```bash
mininet> h2 iperf -s &
mininet> h1 iperf -c h2 -t 5
```
Expected: ~10 Mbps bandwidth (set in topology link config)

---

### Scenario 2: Unauthorized Access (should FAIL)

```bash
mininet> h4 ping -c 4 h1
```
**Expected Output:**
```
PING 10.0.0.1 (10.0.0.1) 56(84) bytes of data.

--- 10.0.0.1 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss
```

```bash
mininet> h4 ping -c 4 h2
# Expected: 100% packet loss

mininet> h4 ping -c 4 h3
# Expected: 100% packet loss
```

---

### Check Flow Tables

In a separate terminal (NOT inside Mininet):
```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
```

**Expected output (after running both scenarios):**

```
# Table-miss rule (always present)
priority=0 actions=CONTROLLER:65535

# Allow rules for authorized traffic (installed dynamically)
priority=10,in_port=1,dl_src=00:00:00:00:00:01,dl_dst=00:00:00:00:00:02 actions=output:2
priority=10,in_port=2,dl_src=00:00:00:00:00:02,dl_dst=00:00:00:00:00:01 actions=output:1

# DROP rule for unauthorized h4
priority=20,in_port=4,dl_src=00:00:00:00:00:04 actions=drop
```

---

### Regression Test: Policy Consistency

This test verifies that the access control policy **remains consistent** even after flow rules are cleared and re-installed.

```bash
# Step 1: Verify initial state
mininet> h1 ping -c 2 h2      # should SUCCEED
mininet> h4 ping -c 2 h1      # should FAIL

# Step 2: Clear all flow rules from switch
# (run in a new terminal)
sudo ovs-ofctl -O OpenFlow13 del-flows s1

# Step 3: Test again — controller re-installs rules
mininet> h1 ping -c 2 h2      # should SUCCEED again
mininet> h4 ping -c 2 h1      # should FAIL again
```

**Result:** Policy is CONSISTENT. The controller re-applies the correct allow/deny rules each time a packet triggers a new packet_in event.

---

## Expected Output Summary

| Test | Src | Dst | Expected | Why |
|------|-----|-----|----------|-----|
| 1.1  | h1  | h2  | ✅ PASS  | Both authorized |
| 1.2  | h2  | h3  | ✅ PASS  | Both authorized |
| 1.3  | h1  | h3  | ✅ PASS  | Both authorized |
| 2.1  | h4  | h1  | ❌ BLOCKED | h4 not in whitelist |
| 2.2  | h4  | h2  | ❌ BLOCKED | h4 not in whitelist |
| 2.3  | h4  | h3  | ❌ BLOCKED | h4 not in whitelist |
| 2.4  | h1  | h4  | ❌ BLOCKED | h4 (dst) not in whitelist |

---

## Log File

All events are saved to `access_log.txt` automatically.

```bash
cat access_log.txt
```

Sample log:
```
2025-01-01 10:00:01  [SWITCH] Switch 1 connected. Table-miss rule installed.
2025-01-01 10:00:10  [ALLOW]  00:00:00:00:00:01 --> 00:00:00:00:00:02  port=1  switch=1
2025-01-01 10:00:15  [BLOCK]  00:00:00:00:00:04 --> 00:00:00:00:00:01  port=4  switch=1  UNAUTHORIZED
2025-01-01 10:00:15  [STATS]  Total=2  Allowed=1  Blocked=1
```

---

## SDN Concepts Used

| Concept | Where Used |
|---------|-----------|
| packet_in event | Every new flow triggers this |
| Flow rules (match-action) | Allow/deny based on src+dst MAC |
| Flow priorities | DROP (20) > Allow (10) > Table-miss (0) |
| MAC learning | Avoid flooding for known destinations |
| idle_timeout / hard_timeout | Automatic rule cleanup |
| OFPFlowMod | Installing rules into switch |
| OFPPacketOut | Forwarding the first packet manually |

---

## Troubleshooting

**Ryu not found:**
```bash
pip install ryu
# or
pip3 install ryu eventlet==0.30.2
```

**Controller not connecting:**
```bash
# Check if port 6633 is open
sudo netstat -tlnp | grep 6633
```

**Mininet cleanup:**
```bash
sudo mn -c
```

**OVS not running:**
```bash
sudo service openvswitch-switch start
```

---

## References

1. Ryu SDN Framework — https://ryu.readthedocs.io/en/latest/
2. OpenFlow 1.3 Specification — https://opennetworking.org/
3. Mininet Walkthrough — https://mininet.org/walkthrough/
4. Ryu packet_in example — https://ryu.readthedocs.io/en/latest/writing_ryu_app.html
5. OVS flow dump — https://www.openvswitch.org/support/dist-docs/ovs-ofctl.8.txt
