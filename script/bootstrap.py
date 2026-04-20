#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import logging

# ==========================================
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='ZTP-BOOTSTRAP: %(levelname)s - %(message)s'
)


def run_command(cmd):

    logging.info("running config: {}".format(cmd))
    try:
        process = subprocess.Popen(
            cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout_data, stderr_data = process.communicate()

        out_str = stdout_data.decode('utf-8').strip() if isinstance(stdout_data, bytes) else stdout_data.strip()
        err_str = stderr_data.decode('utf-8').strip() if isinstance(stderr_data, bytes) else stderr_data.strip()

        if process.returncode != 0:
            logging.error("running failed error: {}".format(cmd, err_str))
            sys.exit(1)

        return out_str
    except Exception as e:
        logging.error("sys error: {}".format(str(e)))
        sys.exit(1)


def get_mac_address(interface="eth0"):
    try:
        with open("/sys/class/net/{}/address".format(interface), "r") as f:
            return f.read().strip()
    except Exception as e:
        logging.error("error when get MAC addr: {}".format(interface, str(e)))
        return "UNKNOWN_MAC"


def get_ip_address(interface="eth0"):
    try:
        out = run_command("ip -4 addr show {}".format(interface))
        for line in out.split('\n'):
            if 'inet ' in line:
                return line.strip().split()[1].split('/')[0]
    except Exception as e:
        logging.error("error with get IP addr: {}".format(interface, str(e)))
    return "UNKNOWN_IP"


def main():
    logging.info("--- start to config SoNIC ---")

    mgmt_mac = get_mac_address("eth0")
    mgmt_ip = get_ip_address("eth0")
    logging.info("ip & mac-> MAC: {}, IP: {}".format(mgmt_mac, mgmt_ip))

    vlans_to_create = [100, 200, 300]
    for vlan_id in vlans_to_create:
        run_command("config vlan add {}".format(vlan_id))
        logging.info("VLAN {} created".format(vlan_id))

    logging.info("saving config to config_db.json...")
    run_command("config save -y")
    logging.info("config saved")

    logging.info("--- ZTP success---")
    sys.exit(0)


if __name__ == "__main__":
    main()

