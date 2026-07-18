from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


INITIAL_PLAYBOOKS = [
    {
        "name": "vyos_router",
        "version": 1,
        "content": (BASE_DIR / "playbook" / "test_playbook.yml").read_text(encoding="utf-8"),
        "is_active": True
    },
    {
        "name": "ovs_l2",
        "version": 1,
        "content": (BASE_DIR / "playbook" / "test_ovs.yml").read_text(encoding="utf-8"),
        "is_active": True
    },
    {
        "name": "veos_l2",
        "version": 1,
        "content": (BASE_DIR / "playbook" / "test_vEOS.yml").read_text(encoding="utf-8"),
        "is_active": True
    },
    {
        "name": "sonic_l2",
        "version": 7,
        "content": (BASE_DIR / "playbook" / "test_sonic.yml").read_text(encoding="utf-8"),
        "is_active": True
    },
    {
        "name": "cisco_l3",
        "version": 1,
        "content": (BASE_DIR / "playbook" / "cisco_l3.yml").read_text(encoding="utf-8"),
        "is_active": True
    }
]
