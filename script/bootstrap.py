#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import logging
import json
import urllib.request

# ==========================================
# 变量配置区
# ==========================================
CONTROLLER_URL = "http://10.10.0.2:8000/device/register"
NEW_USER = "admin"
NEW_PASS = "password"

logging.basicConfig(
    level=logging.INFO,
    format='ZTP-BOOTSTRAP: %(levelname)s - %(message)s'
)


def run_command(cmd, ignore_error=False):
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
            if not ignore_error:
                logging.error("running failed error: {} - {}".format(cmd, err_str))
                sys.exit(1)
            else:
                logging.warning("command returned non-zero (ignored): {} - {}".format(cmd, err_str))
        return out_str
    except Exception as e:
        logging.error("sys error: {}".format(str(e)))
        if not ignore_error:
            sys.exit(1)
        return ""


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




def register_to_controller(ip, mac):
    logging.info("ready to register to Controller...")

    # 构造 JSON Payload，适配控制器的数据结构
    payload = {
        "ip_address": ip,
        "mac": mac,
        "os_type": "sonic",
        "status": "register",
        "device_type": "switch"  # SONiC 作为交换机注册
    }

    logging.info("-> payload: {}".format(json.dumps(payload)))

    # 使用 urllib 原生发送 POST 请求
    # 将字典序列化为 JSON 字节流
    data = json.dumps(payload).encode('utf-8')

    # 构造 HTTP POST 请求
    req = urllib.request.Request(
        url=CONTROLLER_URL,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode('utf-8')
            status_code = response.getcode()
            logging.info("Device registered successfully! HTTP Status: {} - Response: {}".format(status_code, res_body))
    except Exception as e:
        logging.error("Registration request failed: {}".format(str(e)))


def main():
    logging.info("--- start to config SONiC ---")

    # 1. 获取管理口信息
    mgmt_mac = get_mac_address("eth0")
    mgmt_ip = get_ip_address("eth0")
    logging.info("ip & mac-> MAC: {}, IP: {}".format(mgmt_mac, mgmt_ip))

    # 2. 配置 SSH 用户与密码
    logging.info("-> creating/updating SSH account: {} ...".format(NEW_USER))

    # SONiC 官方创建用户的 CLI 命令 (赋予 admin 角色)
    # 使用 ignore_error=True 是因为如果 admin 用户已存在，该命令会报错，我们忽略即可
    run_command("config user add {} -p {} -r admin".format(NEW_USER, NEW_PASS), ignore_error=True)

    # 强制通过底层的 Linux 命令更新密码，确保无论用户是否已存在，密码都能设置成功
    run_command("echo '{}:{}' | chpasswd".format(NEW_USER, NEW_PASS))

    # 3. 保存配置
    logging.info("saving config to config_db.json...")
    run_command("config save -y")
    logging.info("config saved")

    # 4. 向 FastAPI 控制器注册
    register_to_controller(mgmt_ip, mgmt_mac)

    logging.info("--- ZTP success---")
    sys.exit(0)


if __name__ == "__main__":
    main()