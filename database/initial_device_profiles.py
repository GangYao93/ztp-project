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
    },
    {
        "device_type": "switch",
        "os_type": "sonic",
        "playbook_name": "sonic_l2",
        "env_name": "sonic_ssh"
    },
    {
        "device_type": "router",
        "os_type": "cisco_ios",
        "playbook_name": "cisco_l3",
        "env_name": "cisco_ios_network_cli"
    }
]
