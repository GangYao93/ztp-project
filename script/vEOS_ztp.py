#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import logging
import json
import urllib.request
import urllib.error

logging.basicConfig(
    level=logging.INFO,
    format='ARISTA-ZTP: %(levelname)s - %(message)s'
)

ZTP_SERVER_URL = "http://10.10.0.20:8000/device/register"


def run_eos_commands(commands_list):
    """通过 Arista 内部的 FastCli 批量执行配置命令"""
    cmd_string = "\n".join(commands_list) + "\n"
    logging.info("Executing EOS commands via FastCli...")

    try:
        # 提权并进入配置模式执行命令
        process = subprocess.Popen(
            ["FastCli", "-p", "15", "-c", cmd_string],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout_data, stderr_data = process.communicate()

        if process.returncode != 0:
            logging.error(f"FastCli failed: {stderr_data.decode('utf-8')}")
            sys.exit(1)

        return stdout_data.decode('utf-8')
    except Exception as e:
        logging.error(f"Failed to execute FastCli: {str(e)}")
        sys.exit(1)


def get_mac_address(interface="Management1"):
    """获取 Arista 管理口的 MAC 地址"""
    try:
        with open(f"/sys/class/net/{interface}/address", "r") as f:
            return f.read().strip()
    except:
        return "UNKNOWN_MAC"


def get_ip_address(interface="Management1"):
    """通过 ip 命令获取管理口 IP"""
    try:
        out = subprocess.check_output(f"ip -4 addr show {interface}", shell=True).decode('utf-8')
        for line in out.split('\n'):
            if 'inet ' in line:
                return line.strip().split()[1].split('/')[0]
    except Exception as e:
        return "UNKNOWN_IP"


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
    req = urllib.request.Request(url=server_url, data=data, method='POST', headers={'Content-Type': 'application/json'})

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            logging.info(f"Registered successfully! HTTP {response.getcode()}")
    except Exception as e:
        logging.error(f"Registration failed: {str(e)}")


def main():
    logging.info("--- Starting Arista ZTP Bootstrap ---")

    mgmt_mac = get_mac_address("Management1")
    mgmt_ip = get_ip_address("Management1")
    logging.info(f"Device Info -> MAC: {mgmt_mac}, IP: {mgmt_ip}")

    eos_config = [
        "configure",
        "username ansible privilege 15 secret ansible",

        "management api http-commands",
        "no shutdown",
        "vrf default",
        "exit",
        "end",
        "write memory"
    ]
    run_eos_commands(eos_config)
    logging.info("Basic configuration and eAPI applied successfully.")

    register_device(ZTP_SERVER_URL, mgmt_mac, mgmt_ip)

    logging.info("--- ZTP Script Completed Successfully ---")

    # 正常退出 (Exit 0 会告诉 EOS ZTP 已成功完成，它将自动禁用 ZTP 并重启相关进程)
    sys.exit(0)


if __name__ == "__main__":
    main()
