# Python modules
import sys
import os

# RapidChiplet modules
import helpers as hlp
import create_plots as cp
import visualizer as vis
import rapidchiplet as rc

def run_native_results():
    # Change this prefix to whatever you want your final graphs and files to be named!
    PROJECT_PREFIX = "chiplet experiments"

    print("==================================================")
    print(f" Running {PROJECT_PREFIX.upper()} Experiments ")
    print("==================================================")

    # Define the three architectures using your new prefix
    architectures = [
        {"design_file": "design_shared.json", "name": f"{PROJECT_PREFIX}_shared"},
        {"design_file": "design_distributed.json", "name": f"{PROJECT_PREFIX}_distributed"},
        {"design_file": "design_hybrid.json", "name": f"{PROJECT_PREFIX}_hybrid"}
    ]

    # Ensure output directories exist
    for d in ["results", "images", "plots"]:
        os.makedirs(d, exist_ok=True)

    for arch in architectures:
        print(f"\nEvaluating: {arch['name']}...")

        # 1. Load the design
        design = hlp.read_json(arch["design_file"])

        # 2. Configure RapidChiplet Core Inputs
        inputs = {"design": design, "verbose": True, "validate": False}
        intermediates = {}

        # Enable the specific metrics needed for your hardware tables
        do_compute = {
            "latency": True,
            "throughput": True,
            "area_summary": True,
            "power_summary": True,
            "link_summary": True,
            "cost": False,
            "booksim_simulation": False
        }

        results_file_name = f"results_{arch['name']}.json"

        # 3. Run RapidChiplet Natively
        print(f" -> Computing metrics for {arch['name']}...")
        results = rc.rapidchiplet(inputs, intermediates, do_compute, results_file_name, verbose=False, validate=False)

        # Save and read the results (formatting fix required by the plotting module)
        results_path = f"./results/{results_file_name}"
        hlp.write_json(results_path, results)
        results = hlp.read_json(results_path)

        # 4. Visualize the Physical Layout (Saves to ./images/)
        print(f" -> Generating 2D layout visualization for {arch['name']}...")
        vis_inputs = {"design": design, "verbose": False, "validate": False}
        vis.visualize_design(vis_inputs, arch["name"], show_chiplet_id=True, show_phy_id=False)

        # 5. Create the Latency vs. Load Plot (Saves to ./plots/)
        print(f" -> Generating network saturation plot for {arch['name']}...")
        cp.create_latency_vs_load_plot(results)

    print("\n==================================================")
    print(" All native evaluations complete! ")
    print(" Check ./results/, ./images/, and ./plots/ ")
    print("==================================================")

if __name__ == "__main__":
    run_native_results()
