import rapidchiplet as rc
import helpers as hlp
import os

# Create a custom booksim config to get precise readings across the 0.01-0.40 band
os.makedirs("inputs/booksim_configs", exist_ok=True)
bsc = {
    "mode": "traffic",
    "precision": 0.01,
    "saturation_factor": 10.0
}
hlp.write_json("inputs/booksim_configs/bsc_ad.json", bsc)

# Update design files to use this config
for arch in ["ad_dist", "ad_shared"]:
    design_path = f"inputs/designs/design_{arch}.json"
    design = hlp.read_json(design_path)
    design["booksim_config"] = "inputs/booksim_configs/bsc_ad.json"
    design["traffic_by_chiplet"] = f"inputs/traffic_by_chiplet/traffic_{arch}.json"
    design["traffic_by_unit"] = f"inputs/traffic_by_chiplet/traffic_{arch}_unit.json"
    hlp.write_json(design_path, design)

    print(f"\n--- Running evaluation for {arch} ---")
    inputs = {"design": design, "verbose": False, "validate": False}
    intermediates = {}
    do_compute = {
        "latency": True,
        "throughput": True,
        "area_summary": True,
        "power_summary": True,
        "link_summary": True,
        "cost": False,
        "booksim_simulation": True
    }
    
    results_file_name = f"results_{arch}.json"
    results = rc.rapidchiplet(inputs, intermediates, do_compute, results_file_name, verbose=True, validate=False)
    
    # Format fix
    results_path = f"./results/{results_file_name}"
    hlp.write_json(results_path, results)
    
    # Print the specific load curve
    print(f"\n[BookSim Trace Results for {arch}]")
    if "booksim_simulation" in results:
        loads = sorted([float(x) for x in results["booksim_simulation"].keys() if hlp.is_float(x)])
        for load in loads:
            if load <= 0.45:
                lat = results["booksim_simulation"][load]["packet_latency"]["avg"]
                print(f"  Load: {load:.3f} -> Latency: {lat:.1f} cycles")
            
print("\nEvaluations complete.")
