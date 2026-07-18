INITIAL_ANSIBLE_ENVS = [
    {
        "name": "vyos_network_cli",
        "version": 1,
        "is_active": True,
        "env_json": {
            "ansible_connection": "network_cli",
            "ansible_network_os": "vyos.vyos.vyos"
        }
    },
    {
        "name": "ovs_ssh",
        "version": 1,
        "is_active": True,
        "env_json": {
            "ansible_connection": "ssh",
            "ansible_become": "yes",
            "ansible_become_method": "sudo"
        }
    },
    {
        "name": "eos_httpapi",
        "version": 1,
        "is_active": True,
        "env_json": {
            "ansible_connection": "httpapi",
            "ansible_network_os": "arista.eos.eos",
            "ansible_httpapi_use_ssl": "yes",
            "ansible_httpapi_validate_certs": "no",
            "ansible_become": "yes",
            "ansible_become_method": "enable"
        }
    },
    {
        "name": "sonic_ssh",
        "version": 2,
        "is_active": True,
        "env_json": {
            "ansible_connection": "ssh",
            "ansible_become": "yes",
            "ansible_become_method": "sudo"
        }
    },
    {
        "name": "cisco_ios_network_cli",
        "version": 1,
        "is_active": True,
        "env_json": {
            "ansible_connection": "ansible.netcommon.network_cli",
            "ansible_network_os": "cisco.ios.ios",
            "ansible_network_cli_ssh_type": "paramiko",
            "ansible_connect_timeout": 30,
            "ansible_command_timeout": 60
        }
    }
]
