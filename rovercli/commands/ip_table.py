DEVICES = [
    ("Jetson", "192.168.1.5", "jet"),
    ("Rover Onboard Computer", "192.168.1.4", "rover"),
    ("Control Base Station", "192.168.1.50", "cbs"),
    ("Comms Pi", "192.168.1.51", "comms_pi"),
    ("Relay", "192.168.1.22", "relay"),
    ("Onboard Antenna", "192.168.1.21", "rv_bullet"),
    ("Dish", "192.168.1.20", "dish"),
    ("Ben's laptop", "192.168.1.55", "ben"),
    ("PTZ Camera", "192.168.1.88", "ptz"),
    ("Relay Pi", "192.168.1.52", "relay_pi"),
    ("Rowan's Laptop", "192.168.1.40", "rowan"),
]


def print_ip_table():
    print("To create an alias, run sudo nano /etc/hosts and paste the following lines:")
    for _, ip, alias in DEVICES:
        print(f"{ip}\t{alias}")

    print(f"\n\n{'Device':<25} {'IP Address':<15} {'Alias':<10}")
    print("-" * 50)
    for name, ip, alias in DEVICES:
        print(f"{name:<25} {ip:<15} {alias:<10}")