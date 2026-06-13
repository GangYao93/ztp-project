INITIAL_DEVICE_CONFIGS = {
    "0c:67:0d:13:00:00": {
        "interfaces": [
            {
                "name": "eth1",
                "address": "192.168.12.1/24"
            },
            {
                "name": "eth2",
                "address": "192.168.13.1/24"
            }
        ],
        "ospf_areas": [
            {
                "area": "0",
                "networks": [
                    "192.168.12.0/24",
                    "192.168.13.0/24"
                ]
            }
        ],
        "dhcp_servers": [
            {
                "pool_name": "pool1",
                "subnet": "192.168.10.0/24",
                "id": "1",
                "gateway": "192.168.10.1",
                "listen_ip": "192.168.12.1",
                "start_ip": "192.168.10.10",
                "end_ip": "192.168.10.254"
            },
            {
                "pool_name": "pool2",
                "subnet": "192.168.20.0/24",
                "id": "2",
                "gateway": "192.168.20.1",
                "listen_ip": "192.168.13.1",
                "start_ip": "192.168.20.10",
                "end_ip": "192.168.20.254"
            }
        ]
    },
    "0c:e7:2f:0d:00:00": {
        "interfaces": [
            {
                "name": "eth1",
                "address": "192.168.12.2/24"
            },
            {
                "name": "eth2",
                "address": "192.168.23.2/24"
            }
        ],
        "sub_interfaces": [
            {"name": "eth3", "vlan_id": "10", "address": "192.168.10.2/24"},
            {"name": "eth3", "vlan_id": "20", "address": "192.168.20.2/24"}
        ],
        "vrrp_groups": [
            {"name": "eth3", "vrid": "1", "vlan_id": "10", "virtual_address": "192.168.10.1/24", "priority": 110},
            {"name": "eth3", "vrid": "2", "vlan_id": "20", "virtual_address": "192.168.20.1/24", "priority": 90}
        ],
        "ospf_areas": [
            {
                "area": "0",
                "networks": [
                    "192.168.12.0/24",
                    "192.168.23.0/24",
                    "192.168.10.0/24",
                    "192.168.20.0/24"
                ]
            }
        ],
        "dhcp_relay": {
            "servers": [
                "192.168.12.1"
            ],
            "listen_interfaces": [
                "eth3.10",
            ],
            "upstream_interfaces": [
                "eth1"
            ]
        }
    },
    "0c:21:dc:c6:00:00": {
        "interfaces": [
            {
                "name": "eth1",
                "address": "192.168.13.3/24"
            },
            {
                "name": "eth2",
                "address": "192.168.23.3/24"
            }
        ],
        "sub_interfaces": [
            {"name": "eth3", "vlan_id": "10", "address": "192.168.10.3/24"},
            {"name": "eth3", "vlan_id": "20", "address": "192.168.20.3/24"}
        ],
        "vrrp_groups": [
            {"name": "eth3", "vrid": "1", "vlan_id": "10", "virtual_address": "192.168.10.1/24", "priority": 90},
            {"name": "eth3", "vrid": "2", "vlan_id": "20", "virtual_address": "192.168.20.1/24", "priority": 110}
        ],
        "ospf_areas": [
            {
                "area": "0",
                "networks": [
                    "192.168.23.0/24",
                    "192.168.13.0/24",
                    "192.168.20.0/24"
                ]
            }
        ],
        "dhcp_relay": {
            "servers": [
                "192.168.13.1"
            ],
            "listen_interfaces": [
                "eth3.20"
            ],
            "upstream_interfaces": [
                "eth1"
            ]
        }
    },
    "0c:18:eb:b9:00:00": {
        "vlans": [
            {
                "id": "10",
                "name": "VLAN10"
            },
            {
                "id": "20",
                "name": "VLAN20"
            }
        ],
        "trunk_port": [
            {
                "name": "eth2",
                "vlans": [10, 20]
            },
            {
                "name": "eth3",
                "vlans": [10, 20]
            },
            {
                "name": "eth4",
                "vlans": [10, 20]
            },
            {
                "name": "eth1",
                "vlans": [10, 20]
            }
        ]
    },
    "0c:18:eb:b8:00:00": {
        "vlans": [
            {
                "id": "10",
                "name": "VLAN10"
            },
            {
                "id": "20",
                "name": "VLAN20"
            }
        ],
        "trunk_port": [
            {
                "name": "eth2",
                "vlans": [10, 20]
            },
            {
                "name": "eth3",
                "vlans": [10, 20]
            },
            {
                "name": "eth4",
                "vlans": [10, 20]
            },
            {
                "name": "eth1",
                "vlans": [10, 20]
            }
        ]
    },
    "0c:18:eb:b7:00:00": {
        "vlans": [
            {
                "id": "10",
                "name": "VLAN10"
            },
            {
                "id": "20",
                "name": "VLAN20"
            }
        ],
        "trunk_port": [
            {
                "name": "eth2",
                "vlans": [10, 20]
            },
            {
                "name": "eth3",
                "vlans": [10, 20]
            },
            {
                "name": "eth4",
                "vlans": [10, 20]
            }
        ],
        "access_port": [
            {
                "name": "eth5",
                "vlan": "10"
            },
            {
                "name": "eth6",
                "vlan": "20"
            }
        ]
    },
    "0c:18:eb:b6:00:00": {
        "vlans": [
            {
                "id": "10",
                "name": "VLAN10"
            },
            {
                "id": "20",
                "name": "VLAN20"
            }
        ],
        "trunk_port": [
            {
                "name": "eth2",
                "vlans": [10, 20]
            },
            {
                "name": "eth3",
                "vlans": [10, 20]
            },
            {
                "name": "eth4",
                "vlans": [10, 20]
            }
        ],
        "access_port": [
            {
                "name": "eth5",
                "vlan": "10"
            },
            {
                "name": "eth6",
                "vlan": "20"
            }
        ]
    }
}
