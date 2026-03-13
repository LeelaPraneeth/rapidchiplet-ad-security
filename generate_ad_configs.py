import json
import os

# Base AD Chiplets
base = {
    "ai_accelerator": {
        "dimensions": {"x": 5.0, "y": 5.0},
        "type": "compute",
        "power": 5000.0,
        "internal_latency": 10,
        "relay": True
    },
    "safety_island": {
        "dimensions": {"x": 3.0, "y": 3.0},
        "type": "compute",
        "power": 1500.0,
        "internal_latency": 5,
        "relay": True
    },
    "sensor_gateway": {
        "dimensions": {"x": 2.0, "y": 4.0},
        "type": "io",
        "power": 2000.0,
        "internal_latency": 3,
        "relay": True
    },
    "dram_controller": {
        "dimensions": {"x": 2.0, "y": 6.0},
        "type": "memory",
        "power": 1200.0,
        "internal_latency": 15,
        "relay": False
    }
}

sec_dist = {
    "dimensions": {"x": 0.35, "y": 0.35},
    "power": 25.0,
    "internal_latency": 24
}

sec_shared = {
    "dimensions": {"x": 1.5, "y": 1.5},
    "type": "security",
    "power": 350.0,
    "internal_latency": 24,
    "relay": True
}

def add_phys(chiplet):
    x = chiplet["dimensions"]["x"]
    y = chiplet["dimensions"]["y"]
    # 4 phys, one on each side
    chiplet["phys"] = [
        {"x": x/2, "y": 0.1, "fraction_bump_area": 0.25},
        {"x": x-0.1, "y": y/2, "fraction_bump_area": 0.25},
        {"x": x/2, "y": y-0.1, "fraction_bump_area": 0.25},
        {"x": 0.1, "y": y/2, "fraction_bump_area": 0.25}
    ]
    chiplet["fraction_power_bumps"] = 0.5
    chiplet["technology"] = "saed32nm"
    chiplet["unit_count"] = 1

# Generate Distributed Chiplets
dist_chiplets = {}
for name, ch in base.items():
    dist_ch = dict(ch)
    dist_ch["dimensions"] = dict(ch["dimensions"])
    if name != "dram_controller":
        dist_ch["dimensions"]["x"] += sec_dist["dimensions"]["x"]
        dist_ch["dimensions"]["y"] += sec_dist["dimensions"]["y"]
        dist_ch["power"] += sec_dist["power"]
        dist_ch["internal_latency"] += sec_dist["internal_latency"]
    add_phys(dist_ch)
    dist_chiplets[name] = dist_ch

# Generate Shared Chiplets
shared_chiplets = {}
for name, ch in base.items():
    shared_ch = dict(ch)
    shared_ch["dimensions"] = dict(ch["dimensions"])
    add_phys(shared_ch)
    shared_chiplets[name] = shared_ch

sh_sec = dict(sec_shared)
sh_sec["dimensions"] = dict(sec_shared["dimensions"])
add_phys(sh_sec)
shared_chiplets["security_hub"] = sh_sec

os.makedirs("inputs/chiplets", exist_ok=True)
with open("inputs/chiplets/chiplets_ad_distributed.json", "w") as f:
    json.dump(dist_chiplets, f, indent=4)

with open("inputs/chiplets/chiplets_ad_shared.json", "w") as f:
    json.dump(shared_chiplets, f, indent=4)

print("Generated chiplets_ad_distributed.json and chiplets_ad_shared.json")
