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
			
	markers = ['o', 's', '^', 'D', 'v', 'p', 'h', '*', '+', 'x']
	colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
	
	for grid, arch_dict in groups.items():
		(fig, ax) = plt.subplots(1, 1, figsize=(7, 5))
		fig.subplots_adjust(left=0.15, right=0.6, top=0.9, bottom=0.15)
		
		valid_curves = 0
		for i, (name, results) in enumerate(arch_dict.items()):
			if "booksim_simulation" not in results:
				continue
				
			loads = [float(x) for x in results["booksim_simulation"].keys() if hlp.is_float(x)]
			if not loads:
				continue
				
			loads = sorted(loads)
			latencies = [results["booksim_simulation"][str(load)]["packet_latency"]["avg"] for load in loads]
			
			clean_name = name.replace("oca_", "").replace(f"_{grid}", "").replace("_", " ").title()
			ax.plot(loads, latencies, marker=markers[i % len(markers)], color=colors[i % len(colors)], label=clean_name, markersize=4, zorder=3)
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

	
	








