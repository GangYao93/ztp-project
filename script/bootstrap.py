#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import shlex
import subprocess
import sys
import urllib.request

CONTROLLER_URL = "http://10.10.0.2:8000/device/register"
NEW_USER = "ansible"
NEW_PASS = "Ansible@123"

logging.basicConfig(
    level=logging.INFO,
    format="ZTP-BOOTSTRAP: %(levelname)s - %(message)s"
)


def run_command(cmd, ignore_error=False, hide_command=False):
    display_cmd = "<hidden>" if hide_command else cmd
    logging.info("running config: {}".format(display_cmd))
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout_data, stderr_data = process.communicate()

        out_str = stdout_data.decode("utf-8").strip() if isinstance(stdout_data, bytes) else stdout_data.strip()
        err_str = stderr_data.decode("utf-8").strip() if isinstance(stderr_data, bytes) else stderr_data.strip()

        if process.returncode != 0:
            if ignore_error:
                logging.warning("command returned non-zero (ignored): {} - {}".format(display_cmd, err_str))
            else:
                logging.error("running failed error: {} - {}".format(display_cmd, err_str))
                sys.exit(1)
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
        logging.error("error when get MAC addr: {} - {}".format(interface, str(e)))
        return "UNKNOWN_MAC"


def get_ip_address(interface="eth0"):
    try:
        out = run_command("ip -4 addr show {}".format(shlex.quote(interface)))
        for line in out.split("\n"):
            if "inet " in line:
                return line.strip().split()[1].split("/")[0]
    except Exception as e:
        logging.error("error with get IP addr: {} - {}".format(interface, str(e)))
    return "UNKNOWN_IP"


def user_exists(username):
    try:
        with open("/etc/passwd", "r") as f:
            for line in f:
                if line.startswith("{}:".format(username)):
                    return True
    except Exception as e:
        logging.warning("failed to check user {}: {}".format(username, str(e)))
    return False


def configure_ssh_user():
    quoted_user = shlex.quote(NEW_USER)
    quoted_pass = shlex.quote(NEW_PASS)

    logging.info("creating/updating SSH account: {}".format(NEW_USER))

    if not user_exists(NEW_USER):
        run_command(
            "config user add {} -p {} -r admin".format(quoted_user, quoted_pass),
            ignore_error=True,
            hide_command=True
        )

    if not user_exists(NEW_USER):
        logging.info("SONiC config user command unavailable; using Linux useradd for {}".format(NEW_USER))
        run_command("useradd -m -s /bin/bash {}".format(quoted_user))

    run_command(
        "printf '%s:%s\\n' {} {} | chpasswd".format(quoted_user, quoted_pass),
        hide_command=True
    )
    run_command("usermod -aG sudo {}".format(quoted_user), ignore_error=True)
    run_command("usermod -aG admin {}".format(quoted_user), ignore_error=True)
    logging.info("SSH account {} is ready".format(NEW_USER))


def register_to_controller(ip, mac):
    logging.info("ready to register to Controller...")

    payload = {
        "ip_address": ip,
        "mac": mac,
        "os_type": "sonic",
        "status": "register",
        "device_type": "switch",
        "username": NEW_USER,
        "password": NEW_PASS
    }

    safe_payload = payload.copy()
    safe_payload["password"] = "***"
    logging.info("payload: {}".format(json.dumps(safe_payload)))

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=CONTROLLER_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            status_code = response.getcode()
            logging.info("Device registered successfully! HTTP Status: {} - Response: {}".format(status_code, res_body))
    except Exception as e:
        logging.error("Registration request failed: {}".format(str(e)))


def main():
    logging.info("--- start to config SONiC ---")

    mgmt_mac = get_mac_address("eth0")
    mgmt_ip = get_ip_address("eth0")
    logging.info("ip & mac -> MAC: {}, IP: {}".format(mgmt_mac, mgmt_ip))

    configure_ssh_user()

    logging.info("saving config to config_db.json...")
    run_command("config save -y")
    logging.info("config saved")

    register_to_controller(mgmt_ip, mgmt_mac)

    logging.info("--- ZTP success ---")
    sys.exit(0)


if __name__ == "__main__":
    main()
