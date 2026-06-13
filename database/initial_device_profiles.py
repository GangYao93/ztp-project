INITIAL_DEVICE_PROFILES = [
    {
        "device_type": "router",
        "os_type": "vyos",
        "playbook_name": "vyos_router",
        "env_name": "vyos_network_cli"
    },
    {
        "device_type": "switch",
        "os_type": "alpine",
        "playbook_name": "ovs_l2",
        "env_name": "ovs_ssh"
    },
    {
        "device_type": "switch",
        "os_type": "arista_eos",
        "playbook_name": "veos_l2",
        "env_name": "eos_httpapi"
    }
]
