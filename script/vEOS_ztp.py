#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import logging
import json
import urllib.request
import urllib.error
import os

logging.basicConfig(
    level=logging.INFO,
    format='ARISTA-ZTP: %(levelname)s - %(message)s'
)

# 确保 IP 匹配你的控制器地址
ZTP_SERVER_URL = "http://10.10.0.20:8000/device/register"


def run_eos_commands(commands_list):
    cmd_string = "\n".join(commands_list) + "\n"
    logging.info("Executing EOS commands via FastCli...")

    try:
        process = subprocess.Popen(
            ["/usr/bin/FastCli", "-p", "15", "-c", cmd_string],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout_data, stderr_data = process.communicate()

        if process.returncode != 0:
            logging.error(f"FastCli failed: {stderr_data.decode('utf-8')}")
            return False
        return True
    except Exception as e:
        logging.error(f"Failed to execute FastCli: {str(e)}")
        return False


def get_mgmt_info():
    interface = "ma1"
    mac = "UNKNOWN_MAC"
    ip = "UNKNOWN_IP"

    try:
        if os.path.exists(f"/sys/class/net/{interface}/address"):
            with open(f"/sys/class/net/{interface}/address", "r") as f:
                mac = f.read().strip()
    except:
        pass

    try:
        out = subprocess.check_output(f"ip -4 addr show {interface}", shell=True).decode('utf-8')
        for line in out.split('\n'):
            if 'inet ' in line:
                ip = line.strip().split()[1].split('/')[0]
    except:
        pass

    return mac, ip


def register_device(server_url, mac, ip):
    logging.info(f"Registering device to {server_url}")
    payload = {
        "ip_address": ip,
        "mac": mac,
        "os_type": "arista_eos",
        "status": "register",
        "device_type": "switch"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url=server_url,
        data=data,
        method='POST',
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            logging.info(f"Registered successfully! HTTP {response.getcode()}")
            return True
    except Exception as e:
        logging.error(f"Registration failed: {str(e)}")
        return False


def main():
    logging.info("--- Starting Arista ZTP Bootstrap ---")

    mgmt_mac, mgmt_ip = get_mgmt_info()
    logging.info(f"Device Info -> MAC: {mgmt_mac}, IP: {mgmt_ip}")

    eos_config = [
        "configure",
        "username ansible privilege 15 secret ansible",
        "management api http-commands",
        "no shutdown",
        "exit",
        "copy running-config startup-config"
    ]

    if run_eos_commands(eos_config):
        logging.info("Basic configuration and eAPI applied.")

    register_device(ZTP_SERVER_URL, mgmt_mac, mgmt_ip)

    logging.info("--- ZTP Script Completed ---")

    sys.exit(0)


if __name__ == "__main__":
    main()