import os
import sys
import json
import subprocess

# RapidChiplet Native Modules
import helpers as hlp
import create_plots as cp
import visualizer as vis
import rapidchiplet as rc

print("==================================================")
print(" 1. GENERATING OCA HARDWARE CONFIGURATIONS ")
print("==================================================")

PROJECT_PREFIX = "oca_mesh"

# Create required directories
directories = ["inputs/chiplets", "inputs/technologies", "inputs/packagings",
               "inputs/placements", "inputs/topologies", "inputs/routing_tables",
               "inputs/traffic_by_chiplet", "results", "images", "plots"]
for d in directories:
    os.makedirs(d, exist_ok=True)

# --- 1. Static Hardware Data ---
hlp.write_json("inputs/technologies/tech_32nm.json", {
    "saed32nm": {"phy_latency": 2, "wafer_radius": 150.0, "wafer_cost": 3000, "defect_density": 0.001},
    "passive_interposer": {"phy_latency": 1, "wafer_radius": 150.0, "wafer_cost": 800, "defect_density": 0.0005}
})

# FIXED: Added back the irouter and interposer keys to satisfy the RapidChiplet parser
hlp.write_json("inputs/packagings/pack_mesh.json", {
    "link_routing": "manhattan", "link_latency_type": "constant", "link_latency": 1,
    "link_power_type": "constant", "link_power": 1, "packaging_yield": 0.9, "bump_pitch": 0.05,
    "non_data_wires": 12, "is_active": False, "has_interposer": False,
    "latency_irouter": 5, "power_irouter": 0.25, "interposer_technology": "passive_interposer"
})

# Hardware Definitions (Using your Synopsys 32nm verified metrics)
base_pe = {"dimensions": {"x": 8.797, "y": 8.797}, "type": "compute", "fraction_power_bumps": 0.5, "technology": "saed32nm", "relay": True, "phys": [{"x": 4.398, "y": 0.5, "fraction_bump_area": 0.25}, {"x": 8.297, "y": 4.398, "fraction_bump_area": 0.25}, {"x": 4.398, "y": 8.297, "fraction_bump_area": 0.25}, {"x": 0.5, "y": 4.398, "fraction_bump_area": 0.25}], "unit_count": 1}
aes_dist = {"dimensions": {"x": 0.316, "y": 0.316}, "type": "crypto", "fraction_power_bumps": 0.5, "technology": "saed32nm", "power": 18.5, "relay": True, "internal_latency": 22, "phys": [{"x": 0.158, "y": 0.05, "fraction_bump_area": 0.25}, {"x": 0.266, "y": 0.158, "fraction_bump_area": 0.25}, {"x": 0.158, "y": 0.266, "fraction_bump_area": 0.25}, {"x": 0.05, "y": 0.158, "fraction_bump_area": 0.25}], "unit_count": 1}
sec_hub = {"dimensions": {"x": 0.408, "y": 0.408}, "type": "security", "fraction_power_bumps": 0.5, "technology": "saed32nm", "power": 38.138, "relay": True, "internal_latency": 22, "phys": [{"x": 0.204, "y": 0.05, "fraction_bump_area": 0.25}, {"x": 0.358, "y": 0.204, "fraction_bump_area": 0.25}, {"x": 0.204, "y": 0.358, "fraction_bump_area": 0.25}, {"x": 0.05, "y": 0.204, "fraction_bump_area": 0.25}], "unit_count": 1}
mem_node = {"dimensions": {"x": 4.0, "y": 8.0}, "type": "memory", "fraction_power_bumps": 0.5, "technology": "saed32nm", "power": 12.0, "relay": True, "internal_latency": 15, "phys": [{"x": 2.0, "y": 0.5, "fraction_bump_area": 0.25}, {"x": 3.5, "y": 4.0, "fraction_bump_area": 0.25}, {"x": 2.0, "y": 7.5, "fraction_bump_area": 0.25}, {"x": 0.5, "y": 4.0, "fraction_bump_area": 0.25}], "unit_count": 1}

# Write Chiplet Catalogs
hlp.write_json("inputs/chiplets/chiplets_distributed.json", { "compute_pe_bloated": {**base_pe, "dimensions": {"x": 8.807, "y": 8.807}, "power": 39.0, "internal_latency": 26}, "security_hub_control": sec_hub, "memory_node": mem_node })
hlp.write_json("inputs/chiplets/chiplets_hybrid.json", { "compute_pe": {**base_pe, "power": 20.5, "internal_latency": 4}, "security_aes_distributed": aes_dist, "security_hub_control": sec_hub, "memory_node": mem_node })
hlp.write_json("inputs/chiplets/chiplets_shared.json", { "compute_pe_dumb": {**base_pe, "power": 20.5, "internal_latency": 4}, "security_hub_massive": {**sec_hub, "dimensions": {"x": 0.516, "y": 0.516}, "power": 56.638, "internal_latency": 22}, "memory_node": mem_node })

# --- 2. Dynamic Placements & Topologies ---
import generate_topology as topogen

def get_node_type(i, n, arch_type):
    x, y = i % n, i // n
    center = n // 2
    if x == center and y == center: return "security_hub_massive" if arch_type == "shared" else "security_hub_control"
    if (x == center and (y == 0 or y == n-1)) or (y == center and (x == 0 or x == n-1)): return "memory_node"
    if arch_type == "distributed": return "compute_pe_bloated"
    elif arch_type == "shared": return "compute_pe_dumb"
    elif arch_type == "hybrid": return "security_aes_distributed" if i % 3 == 0 else "compute_pe"

grid_sizes = [3, 4, 5, 6, 8, 10, 12, 16]
architectures = ["shared", "distributed", "hybrid"]
topologies = ["mesh", "torus", "folded_torus", "sid_mesh"]
generated_designs = []

for n in grid_sizes:
    for topo_name in topologies:
        topo_file = f"inputs/topologies/topo_{topo_name}_{n}x{n}.json"
        if not os.path.exists(topo_file):
            params = {"rows": n, "cols": n}
            if topo_name == "mesh":
                topodata = topogen.generate_mesh_topology(params)
            elif topo_name == "torus":
                topodata = topogen.generate_torus_topology(params)
            elif topo_name == "folded_torus":
                topodata = topogen.generate_folded_torus_topology(params)
            elif topo_name == "sid_mesh":
                topodata = topogen.generate_sid_mesh_topology(params)
            hlp.write_json(topo_file, topodata)

        for arch in architectures:
            chipsets_payload = hlp.read_json(f"inputs/chiplets/chiplets_{arch}.json")
            placement_payload = {"interposer_routers": [], "chiplets": [{"position": {"x": (i%n)*10.0, "y": (i//n)*10.0}, "rotation": 0, "name": get_node_type(i, n, arch)} for i in range(n*n)]}
            hlp.write_json(f"inputs/placements/place_{n}x{n}_{arch}.json", placement_payload)
            
            # BookSim needs exact unit traffic mathematically. We use the original hotspot generator logic
            center_node = (n // 2) * n + (n // 2)
            import generate_traffic as trgen
            
            traffic_unit = {}
            target_units = chipsets_payload[placement_payload["chiplets"][center_node]["name"]]["unit_count"]
            for src_cid in range(n*n):
                if src_cid == center_node: continue
                src_chiplet = chipsets_payload[placement_payload["chiplets"][src_cid]["name"]]
                for src_uid in range(src_chiplet["unit_count"]):
                    src = (src_cid, src_uid)
                    for dst_uid in range(target_units):
                        dst = (center_node, dst_uid)
                        traffic_unit[(src, dst)] = 0.05 / target_units

            traffic_chip = hlp.convert_by_unit_traffic_to_by_chiplet_traffic(traffic_unit)
            
            hlp.write_json(f"inputs/traffic_by_unit/traffic_{n}x{n}_{arch}.json", traffic_unit)
            hlp.write_json(f"inputs/traffic_by_chiplet/traffic_{n}x{n}_{arch}.json", traffic_chip)

            design_name = f"design_oca_{topo_name}_{n}x{n}_{arch}.json"
            hlp.write_json(design_name, {
                "design_name": f"oca_{topo_name}_{n}x{n}_{arch}",
                "technologies": "inputs/technologies/tech_32nm.json",
                "chiplets": f"inputs/chiplets/chiplets_{arch}.json",
                "placement": f"inputs/placements/place_{n}x{n}_{arch}.json",
                "packaging": "inputs/packagings/pack_mesh.json",
                "topology": topo_file,
                "routing_table": f"inputs/routing_tables/rt_{topo_name}_{n}x{n}.json",
                "traffic_by_unit": f"inputs/traffic_by_unit/traffic_{n}x{n}_{arch}.json",
                "traffic_by_chiplet": f"inputs/traffic_by_chiplet/traffic_{n}x{n}_{arch}.json",
                "trace": "none",
                "booksim_config": "inputs/booksim_configs/example_booksim_config.json"
            })
            generated_designs.append(design_name)

# Generate exact routing tables
routings = set()
for d in generated_designs:
    d_params = d.replace("design_oca_", "").replace(".json", "").split("_")
    # ex: mesh, 3x3, shared
    # ex2: sid, mesh, 3x3, shared
    grid = d_params[-2]
    topo_name = "_".join(d_params[:-2])
    routings.add((topo_name, grid))

for topo_name, n in routings:
    rt_file = f"rt_{topo_name}_{n}"
    if not os.path.exists(f"inputs/routing_tables/{rt_file}.json"):
        print(f" -> Generating Shortest-Path Routing for {topo_name} {n}...")
        # Grab any design matching this topology+grid to pathfind with
        sample_design = next(x for x in generated_designs if f"{topo_name}_{n}" in x)
        subprocess.run(f"{sys.executable} generate_routing.py -df {sample_design} -rtf {rt_file} -ra splif", shell=True)

    # Safety Check
    if not os.path.exists(f"inputs/routing_tables/{rt_file}.json"):
        print(f"\n[CRITICAL ERROR] Routing table {rt_file}.json was not created!")
        sys.exit(1)

print("\n==================================================")
print(" 2. RUNNING NATIVE RAPIDCHIPLET EVALUATION ")
print("==================================================")

all_simulation_results = {}

for design_file in generated_designs:
    arch_name = design_file.replace("design_", "").replace(".json", "")
    print(f"\nEvaluating: {arch_name}...")
    
    # Check if already completed and valid
    results_file_name = f"results_{arch_name}.json"
    results_path = f"./results/{results_file_name}"
    if os.path.exists(results_path):
        res = hlp.read_json(results_path)
        if "throughput" in res and "latency" in res:
            all_simulation_results[arch_name] = res
            continue

    # Load the design
    design = hlp.read_json(design_file)

    inputs = {"design": design, "verbose": False, "validate": False}
    intermediates = {}
    do_compute = {"latency": True, "throughput": True, "area_summary": True, "power_summary": True, "link_summary": True, "cost": False, "booksim_simulation": True}
    results_file_name = f"results_{arch_name}.json"

    # Compute Metrics
    print(f" -> Computing metrics...")
    results = rc.rapidchiplet(inputs, intermediates, do_compute, results_file_name, verbose=False, validate=False)

    # Format fix (required by plotting module)
    results_path = f"./results/{results_file_name}"
    hlp.write_json(results_path, results)
    results = hlp.read_json(results_path)
    
    # Store explicitly for the consolidated load plot
    all_simulation_results[arch_name] = results

    # Visualization (2D Layout)
    print(f" -> Rendering 2D layout visualization to ./images/...")
    vis.visualize_design(inputs, arch_name, show_chiplet_id=True, show_phy_id=False)

# Plotting (Saturation Curve)
print(f"\n -> Rendering consolidated network saturation plot to ./plots/...")
cp.create_latency_vs_load_plot(all_simulation_results)

print("\n==================================================")
print(" All native evaluations complete! ")
print(" Check your ./results/, ./images/, and ./plots/ folders! ")
print("==================================================")
