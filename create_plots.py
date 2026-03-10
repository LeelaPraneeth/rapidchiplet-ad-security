# Python modules
import os
import sys
import argparse
import matplotlib.pyplot as plt

# RapidChiplet modules
import helpers as hlp

def create_latency_vs_load_plot(results_dict, output_name="latency_vs_load"):
	# Group results by grid size to map to individual subplots/files
	groups = {}
	for arch_name, results in results_dict.items():
		# Format example: oca_mesh_4x4_shared
		parts = arch_name.split("_")
		if len(parts) >= 3:
			grid_size = parts[-2]
			if grid_size not in groups:
				groups[grid_size] = {}
			groups[grid_size][arch_name] = results
			
	topo_markers = {
		"mesh": "o", 
		"torus": "s", 
		"folded_torus": "D", 
		"sid_mesh": "v"
	}
	arch_colors = {
		"shared": '#1f77b4',      # blue
		"distributed": '#ff7f0e', # orange
		"hybrid": '#2ca02c'       # green
	}
	
	for grid, arch_dict in groups.items():
		(fig, ax) = plt.subplots(1, 1, figsize=(7, 5))
		fig.subplots_adjust(left=0.15, right=0.6, top=0.9, bottom=0.15)
		
		valid_curves = 0
		for name, results in arch_dict.items():
			if "booksim_simulation" not in results:
				continue
				
			loads = [float(x) for x in results["booksim_simulation"].keys() if hlp.is_float(x)]
			if not loads:
				continue
				
			loads = sorted(loads)
			latencies = [results["booksim_simulation"][str(load)]["packet_latency"]["avg"] for load in loads]
			
			clean_name = name.replace("oca_", "").replace(f"_{grid}", "").replace("_", " ").title()
			
			# Map topology and architectures to specific visuals
			marker = "o"
			for t_name, m in topo_markers.items():
				if t_name in name:
					marker = m
					break
			color = "#000000"
			for a_name, c in arch_colors.items():
				if a_name in name:
					color = c
					break
					
			ax.plot(loads, latencies, marker=marker, color=color, label=clean_name, markersize=4, zorder=3)
			valid_curves += 1
		
		if valid_curves > 0:
			ax.grid(True, linestyle="--", alpha=0.7, zorder=0)
			ax.set_facecolor("#fcfcfc")
			ax.set_xlabel("Injection Rate (Load)", fontsize=11)
			ax.set_ylabel("Average Latency (cycles)", fontsize=11)
			ax.set_title(f"Latency vs Load for {grid} Grids", fontsize=12)
			
			ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Network Configurations", fontsize=8, title_fontsize=9)
			
			filepath = f"plots/{output_name}_{grid}.pdf"
			plt.savefig(filepath, bbox_inches="tight")
			print(f" -> Saved latency vs load curve group to {filepath}")
		
		plt.close(fig)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-rf", "--results_file", type=str, help="Results file to plot", required=True)
	parser.add_argument("-pt", "--plot_type", type=str, help="Type of plot to create", required=True)
	args = parser.parse_args()
	results = hlp.read_json(args.results_file)
	if args.plot_type == "latency_vs_load":
		create_latency_vs_load_plot(results)
	else:	
		print("Invalid plot type \"%s\". Valid plot types are: latency_vs_load" % args.plot_type)

	
	








