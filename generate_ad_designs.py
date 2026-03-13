import json
import os
import generate_topology as topogen

os.makedirs("inputs/placements", exist_ok=True)
os.makedirs("inputs/topologies", exist_ok=True)
os.makedirs("inputs/designs", exist_ok=True)
os.makedirs("inputs/traffic_by_chiplet", exist_ok=True)

# 1. Distributed Placement (2x2)
dist_placement = {
    "interposer_routers": [],
    "chiplets": [
        {"position": {"x": 0.0, "y": 0.0}, "rotation": 0, "name": "ai_accelerator"}, # 0
        {"position": {"x": 15.0, "y": 0.0}, "rotation": 0, "name": "safety_island"}, # 1
        {"position": {"x": 0.0, "y": 15.0}, "rotation": 0, "name": "sensor_gateway"}, # 2
        {"position": {"x": 15.0, "y": 15.0}, "rotation": 0, "name": "dram_controller"} # 3
    ]
}
with open("inputs/placements/place_ad_dist.json", "w") as f:
    json.dump(dist_placement, f, indent=4)

# 2. Distributed Topology (2x2 Mesh using topogen)
dist_topo = topogen.generate_mesh_topology({"rows": 2, "cols": 2})
with open("inputs/topologies/topo_ad_dist.json", "w") as f:
    json.dump(dist_topo, f, indent=4)

# 3. Shared Placement (Star topology with security_hub at center)
shared_placement = {
    "interposer_routers": [],
    "chiplets": [
        {"position": {"x": 15.0, "y": 15.0}, "rotation": 0, "name": "security_hub"}, # 0
        {"position": {"x": 15.0, "y": 30.0}, "rotation": 0, "name": "ai_accelerator"}, # 1
        {"position": {"x": 15.0, "y": 0.0}, "rotation": 0, "name": "safety_island"}, # 2
        {"position": {"x": 0.0, "y": 15.0}, "rotation": 0, "name": "sensor_gateway"}, # 3
        {"position": {"x": 30.0, "y": 15.0}, "rotation": 0, "name": "dram_controller"} # 4
    ]
}
with open("inputs/placements/place_ad_shared.json", "w") as f:
    json.dump(shared_placement, f, indent=4)

# 4. Shared Topology (Star)
shared_topo = [
    {"ep1": {"type": "chiplet", "outer_id": 0, "inner_id": 0}, "ep2": {"type": "chiplet", "outer_id": 1, "inner_id": 2}, "color": "blue"},
    {"ep1": {"type": "chiplet", "outer_id": 0, "inner_id": 1}, "ep2": {"type": "chiplet", "outer_id": 2, "inner_id": 0}, "color": "blue"},
    {"ep1": {"type": "chiplet", "outer_id": 0, "inner_id": 2}, "ep2": {"type": "chiplet", "outer_id": 3, "inner_id": 1}, "color": "blue"},
    {"ep1": {"type": "chiplet", "outer_id": 0, "inner_id": 3}, "ep2": {"type": "chiplet", "outer_id": 4, "inner_id": 3}, "color": "blue"}
]
with open("inputs/topologies/topo_ad_shared.json", "w") as f:
    json.dump(shared_topo, f, indent=4)

# 5. Global Uniform Traffic
traffic = {
    "distribution": "uniform",
    "multiplier": 1.0,
    "pattern": "custom"
}
with open("inputs/traffic_by_chiplet/traffic_ad.json", "w") as f:
    json.dump(traffic, f, indent=4)

# 6. Design JSONs
dist_design = {
    "design_name": "ad_distributed",
    "technologies": "inputs/technologies/tech_32nm.json",
    "chiplets": "inputs/chiplets/chiplets_ad_distributed.json",
    "placement": "inputs/placements/place_ad_dist.json",
    "packaging": "inputs/packagings/pack_mesh.json", # Standard packaging
    "topology": "inputs/topologies/topo_ad_dist.json",
    "routing_table": "inputs/routing_tables/rt_ad_dist.json",
    "traffic_by_unit": "none",
    "traffic_by_chiplet": "inputs/traffic_by_chiplet/traffic_ad.json",
    "trace": "none",
    "booksim_config": "none"
}
with open("inputs/designs/design_ad_dist.json", "w") as f:
    json.dump(dist_design, f, indent=4)

shared_design = {
    "design_name": "ad_shared",
    "technologies": "inputs/technologies/tech_32nm.json",
    "chiplets": "inputs/chiplets/chiplets_ad_shared.json",
    "placement": "inputs/placements/place_ad_shared.json",
    "packaging": "inputs/packagings/pack_mesh.json",
    "topology": "inputs/topologies/topo_ad_shared.json",
    "routing_table": "inputs/routing_tables/rt_ad_shared.json",
    "traffic_by_unit": "none",
    "traffic_by_chiplet": "inputs/traffic_by_chiplet/traffic_ad.json",
    "trace": "none",
    "booksim_config": "none"
}
with open("inputs/designs/design_ad_shared.json", "w") as f:
    json.dump(shared_design, f, indent=4)

print("Generated all design, placement, and topology files.")
