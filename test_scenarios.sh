#!/bin/bash
# ===================================================
# test_scenarios.sh
# Project : SDN-Based Access Control System
# SRN     : PES1UG24CS280
# ===================================================
#
# HOW TO USE:
#   After starting Ryu + Mininet, open Mininet CLI
#   and run commands from SCENARIO 1 and SCENARIO 2
#   manually, OR run this from inside Mininet:
#       mininet> sh test_scenarios.sh
#
# NOTE: This script shows what to run and expected output.
#       Run each command in the Mininet CLI directly.
# ===================================================

echo ""
echo "=================================================="
echo " SDN ACCESS CONTROL - TEST SCENARIOS"
echo " SRN: PES1UG24CS280"
echo "=================================================="
echo ""

echo "--------------------------------------------------"
echo " SCENARIO 1: Authorized hosts communicating"
echo " Expected : PING SUCCEEDS (0% packet loss)"
echo "--------------------------------------------------"
echo ""
echo "Test 1.1 : h1 --> h2 (both authorized)"
echo "  Command : h1 ping -c 4 h2"
echo "  Expect  : 0% packet loss"
echo ""
echo "Test 1.2 : h2 --> h3 (both authorized)"
echo "  Command : h2 ping -c 4 h3"
echo "  Expect  : 0% packet loss"
echo ""
echo "Test 1.3 : h1 --> h3 (both authorized)"
echo "  Command : h1 ping -c 4 h3"
echo "  Expect  : 0% packet loss"
echo ""
echo "Test 1.4 : iperf bandwidth between h1 and h2"
echo "  Command : h2 iperf -s &"
echo "            h1 iperf -c h2 -t 5"
echo "  Expect  : Shows bandwidth ~10 Mbps"
echo ""

echo "--------------------------------------------------"
echo " SCENARIO 2: Unauthorized host trying to access"
echo " Expected : PING FAILS (100% packet loss)"
echo "--------------------------------------------------"
echo ""
echo "Test 2.1 : h4 --> h1 (h4 is unauthorized)"
echo "  Command : h4 ping -c 4 h1"
echo "  Expect  : 100% packet loss"
echo ""
echo "Test 2.2 : h4 --> h2 (h4 is unauthorized)"
echo "  Command : h4 ping -c 4 h2"
echo "  Expect  : 100% packet loss"
echo ""
echo "Test 2.3 : h4 --> h3 (h4 is unauthorized)"
echo "  Command : h4 ping -c 4 h3"
echo "  Expect  : 100% packet loss"
echo ""
echo "Test 2.4 : h1 --> h4 (h4 not in whitelist)"
echo "  Command : h1 ping -c 4 h4"
echo "  Expect  : 100% packet loss"
echo "  Reason  : dst not in whitelist"
echo ""

echo "--------------------------------------------------"
echo " FLOW TABLE CHECK (run in a NEW terminal)"
echo "--------------------------------------------------"
echo ""
echo "  Command : sudo ovs-ofctl -O OpenFlow13 dump-flows s1"
echo "  Look for: priority=20 with no actions (DROP rules)"
echo "            priority=10 with output:port (ALLOW rules)"
echo ""

echo "--------------------------------------------------"
echo " REGRESSION TEST: Policy consistency check"
echo "--------------------------------------------------"
echo ""
echo "Step 1: Run test 1.1 (h1 ping h2) - should SUCCEED"
echo "Step 2: Run test 2.1 (h4 ping h1) - should FAIL"
echo "Step 3: Clear flow rules:"
echo "        sudo ovs-ofctl -O OpenFlow13 del-flows s1"
echo "Step 4: Re-run test 1.1 - should SUCCEED again"
echo "Step 5: Re-run test 2.1 - should FAIL again"
echo "Result: Policy is CONSISTENT across rule reinstalls"
echo ""

echo "=================================================="
echo " Check access_log.txt for full event log"
echo " Command: cat access_log.txt"
echo "=================================================="
