# Python modules
import os
import sys
import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# RapidChiplet modules
import helpers as hlp
import global_config as cfg

def read_results(prefix, suffix, n_units):
	data = {}
	results_lat = hlp.read_json("results/%slatency%s.json" % (prefix, suffix))
	results_tp = hlp.read_json("results/%sthroughput%s.json" % (prefix, suffix))
	results_bs = hlp.read_json("results/%sbooksim%s.json" % (prefix, suffix))
	results_link = hlp.read_json("results/%slinks%s.json" % (prefix, suffix))
	data["latency"] = results_lat["latency"]["avg"]
	data["throughput"] = results_tp["throughput"]["aggregate_throughput"]
	data["bs_latency"] = results_bs["booksim_simulation"]["0.001"]["packet_latency"]["avg"]
	data["runtime_lat"] = results_lat["latency"]["time_taken"]
	data["runtime_tp"] = results_tp["throughput"]["time_taken"]
	data["bs_runtime_lat"] = results_bs["booksim_simulation"]["0.001"]["total_run_time"]
	data["bs_runtime_tp"] = sum([results_bs["booksim_simulation"][x]["total_run_time"] for x in results_bs["booksim_simulation"].keys() if hlp.is_float(x)])
	# We need to transform the injection rate reported by BookSim into the aggregate throughput reported by RapidChiplet
	max_inj_rate = max([float(x) for x in results_bs["booksim_simulation"].keys() if hlp.is_float(x)])
	if results_link["link_summary"]["bandwidths"]["min"] == results_link["link_summary"]["bandwidths"]["max"]:
		link_bw = results_link["link_summary"]["bandwidths"]["min"]
	else:
		print("ERROR: Link bandwidths are not uniform")
		sys.exit(1)
	data["bs_throughput"] = max_inj_rate * link_bw * n_units
	return data	
			
def create_evaluation_plot():
	# Plot settings
	colors = cfg.colors
	markers = ["o","s","D","p"]
	# Load the BookSim part of the evaluation.
	# Parameters should be identical for the latency and throughput parts.
	experiment = hlp.read_json("experiments/evaluation_booksim.json")
	experiment_name = "evaluation"
	del experiment["exp_name"]
	del experiment["metrics"]
	(base_params, ranged_params) = re.split_parameters(experiment)
	units_per_chiplet = base_params["units_per_chiplet"]
	scales = ranged_params["grid_scale"]
	topologies = ranged_params["topology"]
	traffics = ranged_params["traffic_pattern"]
	# Create a list of files that contain the results needed for the accuracy plot
	data = []
	for topology in topologies:
		for scale in scales:
			for traffic in traffics:
				prefix = experiment_name + "_"
				suffix = "-%s-%s-%s" % (topology, scale, traffic)
				n_chiplets = int(scale.split("x")[0]) * int(scale.split("x")[1])
				n_units = n_chiplets * units_per_chiplet
				entry = read_results(prefix, suffix, n_units)
				entry["topology"] = topology
				entry["scale"] = scale
				entry["traffic"] = traffic
				data.append(entry)
	# Create the plot
	(fig, ax) = plt.subplots(4, 4, figsize=(10, 12))
	fig.subplots_adjust(left=0.1, right=0.99, top=0.975, bottom=0.075, hspace=0.1, wspace=0.1)
	limits = [[float("inf"),-float("inf")] for i in range(4)]
	values = [("Latency Error", []), ("Latency Speedup", []), ("Throughput Error", []), ("Throughput Speedup", [])]
	# Iterate through traffic patterns (subplots):
	for (i, traffic) in enumerate(traffics):
		ax[0][i].set_title(" ".join([x.capitalize() for x in traffic.split("_")]))
		# Iterate through topologies (lines):
		for (j, topology) in enumerate(topologies):
			filtered_data = [x for x in data if x["traffic"] == traffic and x["topology"] == topology]
			filtered_data = sorted(filtered_data, key=lambda x: int(x["scale"].split("x")[0]))
			xvals = [x["scale"] for x in filtered_data]
			lat_err = [(x["latency"] / x["bs_latency"] -1.0) * 100 for x in filtered_data]
			tp_err = [(x["throughput"] / x["bs_throughput"] -1.0) * 100 for x in filtered_data]
			lat_spu = [(x["bs_runtime_lat"] / x["runtime_lat"] if x["runtime_lat"] > 0 else float("nan")) for x in filtered_data]
			tp_spu = [(x["bs_runtime_tp"] / x["runtime_tp"] if x["runtime_tp"] > 0 else float("nan")) for x in filtered_data]
			metrics = [lat_err, lat_spu, tp_err, tp_spu]
			for (k, metric) in enumerate(metrics):
				ax[k][i].plot(xvals, metric, label=topology, marker=markers[j], color=colors[j])
				limits[k][0] = min(limits[k][0], min(metric))
				limits[k][1] = max(limits[k][1], max(metric))
				values[k][1].append(sum([abs(x) for x in metric]) / len(metric))
				# Add a horizontal line at 0 for the error plots
				if k % 2 == 0:
					ax[k][i].axhline(0, color="black", linestyle="--")
	# Add average per subplot
	for i in range(4):
		for j in range(len(traffics)):
			vals = values[i][1][4*j:4*(j+1)]
			avg = sum(vals) / len(vals)
			if "Error" in values[i][0]:
				ax[i][j].text(0.5, 0.95, "Average: %.2f%%" % avg, ha="center", va="top", transform=ax[i][j].transAxes, fontweight="bold")
			else:
				ax[i][j].text(0.5, 0.95, "Average: %.0fx" % avg, ha="center", va="top", transform=ax[i][j].transAxes, fontweight="bold")

	# Y-labels
	ax[0][0].set_ylabel("Latency Error [%]")
	ax[1][0].set_ylabel("Latency Speedup")
	ax[2][0].set_ylabel("Throughput Error [%]")
	ax[3][0].set_ylabel("Throughput Speedup")
	# General y-axis settings
	for (i, limit) in enumerate(limits):
		for (j, traffic) in enumerate(traffics):
			# Y-Limit
			ax[i][j].set_ylim(limit[0], limit[1])
			# Grid
			ax[i][j].grid(which="both", color = "#666666")
			# Y-Axis in percent for error plots
			if i == 3:
				ax[i][j].set_yscale("log")
			ax[i][j].set_yticks(ax[i][j].get_yticks()[1:-1])
			if i % 2 == 0:
				ax[i][j].yaxis.set_major_formatter(mtick.PercentFormatter())
			# Only show Y-Tick labels on the left-most subplots
			if j > 0:
				ax[i][j].set_yticklabels([])
	# General x-axis settings
	for i in range(4):
		for j in range(len(traffics)):
			ax[i][j].set_xticks(range(len(scales)))
			if i == 3:	
				ax[i][j].set_xlabel("Number of Chiplets")
				ax[i][j].set_xticklabels(scales, rotation=90)
			else:
				ax[i][j].set_xticklabels([])
	# Save the plot
	plt.savefig("plots/evaluation.pdf")
	# Print the average values
	for (name, values) in values:
		print("Average %s: %.3f %s" % (name, sum(values) / len(values), "%" if "Error" in name else ""))

def create_extended_evaluation_plot():
	colors = cfg.colors
	markers = ["o","s","D","p"]
	experiment = hlp.read_json("experiments/evaluation_booksim.json")
	experiment_name = "evaluation"
	del experiment["exp_name"]
	del experiment["metrics"]
	(base_params, ranged_params) = re.split_parameters(experiment)
	units_per_chiplet = base_params["units_per_chiplet"]
	scales = ranged_params["grid_scale"]
	topologies = ranged_params["topology"]
	traffics = ranged_params["traffic_pattern"]
	# Create a list of files that contain the results needed for the accuracy plot
	data = []
	for topology in topologies:
		for scale in scales:
			for traffic in traffics:
				prefix = experiment_name + "_"
				suffix = "-%s-%s-%s" % (topology, scale, traffic)
				n_chiplets = int(scale.split("x")[0]) * int(scale.split("x")[1])
				n_units = n_chiplets * units_per_chiplet
				entry = read_results(prefix, suffix, n_units)
				entry["topology"] = topology
				entry["scale"] = scale
				entry["traffic"] = traffic
				data.append(entry)
	# Create the plot
	(fig, ax) = plt.subplots(8, 4, figsize=(10, 24))
	fig.subplots_adjust(left=0.1, right=0.99, top=0.975, bottom=0.05, hspace=0.1, wspace=0.1)
	limits = [[float("inf"),-float("inf")] for i in range(8)]
	values = [("Latency", []), ("BookSim Latency", []), ("Throughput", []), ("BookSim Throughput", []), ("Latency Runtime", []), ("BookSim Latency Runtime", []), ("Throughput Runtime", []), ("BookSim Throughput Runtime", [])]
	# Iterate through traffic patterns (subplots):
	for (i, traffic) in enumerate(traffics):
		ax[0][i].set_title(" ".join([x.capitalize() for x in traffic.split("_")]))
		# Iterate through topologies (lines):
		for (j, topology) in enumerate(topologies):
			filtered_data = [x for x in data if x["traffic"] == traffic and x["topology"] == topology]
			filtered_data = sorted(filtered_data, key=lambda x: int(x["scale"].split("x")[0]))
			xvals = [x["scale"] for x in filtered_data]
			lat = [x["latency"] for x in filtered_data]
			bs_lat = [x["bs_latency"] for x in filtered_data]
			tp = [x["throughput"] for x in filtered_data]
			bs_tp = [x["bs_throughput"] for x in filtered_data]
			lat_rt = [x["runtime_lat"] for x in filtered_data]
			bs_lat_rt = [x["bs_runtime_lat"] for x in filtered_data]
			tp_rt = [x["runtime_tp"] for x in filtered_data]
			bs_tp_rt = [x["bs_runtime_tp"] for x in filtered_data]
			#print("RC-Lat-Runtime for %s and %s: From %.2f to %.2f" % (topology, traffic, min(lat_rt), max(lat_rt)))
			#print("BS-TP-Runtime for %s and %s: From %.2f to %.2f" % (topology, traffic, min(bs_lat_rt), max(bs_lat_rt)))
			#print("RC-Lat-Runtime for %s and %s: From %.2f to %.2f" % (topology, traffic, min(tp_rt), max(tp_rt)))
			print("BS-TP-Runtime for %s and %s: From %.2f to %.2f" % (topology, traffic, min(bs_tp_rt), max(bs_tp_rt)))

			metrics = [lat, bs_lat, tp, bs_tp, lat_rt, bs_lat_rt, tp_rt, bs_tp_rt]
			for (k, metric) in enumerate(metrics):
				ax[k][i].plot(xvals, metric, label=topology, marker=markers[j], color=colors[j])
				limits[k][0] = min(limits[k][0], min(metric))
				limits[k][1] = max(limits[k][1], max(metric))
				values[k][1].append(sum([abs(x) for x in metric]) / len(metric))
				# Add a horizontal line at 0 for the error plots
				if k % 2 == 0:
					ax[k][i].axhline(0, color="black", linestyle="--")
	# Y-labels
	ax[0][0].set_ylabel("Latency [cycles]")
	ax[1][0].set_ylabel("BookSim Latency [cycles]")
	ax[2][0].set_ylabel("Throughput [flits/cycle]")
	ax[3][0].set_ylabel("BookSim Throughput [flits/cycle]")
	ax[4][0].set_ylabel("Latency Runtime [s]")
	ax[5][0].set_ylabel("BookSim Latency Runtime [s]")
	ax[6][0].set_ylabel("Throughput Runtime [s]")	
	ax[7][0].set_ylabel("BookSim Throughput Runtime [s]")
	# General y-axis settings
	for (i, limit) in enumerate(limits):
		lmt = max(limits[2 * (i//2)][1], abs(limits[2 * (i//2)+1][1])) if i < 4 else limits[i][1]
		for (j, traffic) in enumerate(traffics):
			# Y-Limit
			ax[i][j].set_ylim(0, lmt)
			# Grid
			ax[i][j].grid(which="both")
			ax[i][j].set_yticks(ax[i][j].get_yticks()[1:-1])
			# Only show Y-Tick labels on the left-most subplots
			if j > 0:
				ax[i][j].set_yticklabels([])
	# General x-axis settings
	for i in range(8):
		for j in range(len(traffics)):
			ax[i][j].set_xticks(range(len(scales)))
			if i == 7:	
				ax[i][j].set_xlabel("Number of Chiplets")
				ax[i][j].set_xticklabels(scales, rotation=90)
			else:
				ax[i][j].set_xticklabels([])
	# Save the plot
	plt.savefig("plots/extended_evaluation.pdf")
	# Print the average values
	for (name, values) in values:
		print("Average %s: %.3f %s" % (name, sum(values) / len(values), "%" if "Error" in name else ""))

def create_case_study_plot():
	data = []
	# Read all files in the results directory
	for file in os.listdir("results"):
		if file.startswith("results_oca_") and file.endswith(".json"):
			results = hlp.read_json("results/%s" % file)
			
			if "booksim_simulation" not in results:
				continue
				
			loads = [float(x) for x in results["booksim_simulation"].keys() if hlp.is_float(x)]
			if not loads:
				continue
			max_load = str(max(loads))
			
			lat = results["booksim_simulation"][max_load]["packet_latency"]["avg"]
			tp = float(max_load) * 100  # Proxy load index for scaled throughput comparison
			area = results["area_summary"]["total_chiplet_area"] * 1e-2	# mm^2 to cm^2
			config_str = file.replace("results_oca_", "").replace(".json", "")
			config = [config_str]
			entry = {"latency": lat, "throughput": tp, "area": area, "config": config}
			data.append(entry)
	print("Total number of points: %d" % len(data))
	# Remove duplicates and close-to-duplicates since 65k points leads to a too large PDF
	unique_points = []
	filtered_data = []
	for entry in data:
		lat = round(entry["latency"], 0)
		tp = round(entry["throughput"], 0)
		area = round(entry["area"], 1)
		point = (lat, tp, area)
		if point not in unique_points:
			unique_points.append(point)
			filtered_data.append(entry)
	print("Number of unique points: %d" % len(filtered_data))
	data = filtered_data
	# Create the plot
	(fig, ax) = plt.subplots(1, 1, figsize=(7.5, 4.5))
	fig.subplots_adjust(left=0.1, right=0.6, top=0.9, bottom=0.15)
	areas_raw = [x["area"] for x in data]
	(min_area, max_area) = (min(areas_raw), max(areas_raw))
	
	areas_sorted = sorted(areas_raw)
	vmin_area = areas_sorted[int(len(areas_sorted) * 0.05)]
	vmax_area = areas_sorted[int(len(areas_sorted) * 0.95)]
	norm = plt.Normalize(vmin=vmin_area, vmax=vmax_area)
	
	# Mapping markers to architectures instead of topology
	arch_markers = {
		"shared": "o", 
		"distributed": "s", 
		"hybrid": "D"
	}
	
	import matplotlib.lines as mlines
	legend_handles = []
	
	for arch_name, marker in arch_markers.items():
		group_data = [x for x in data if arch_name in x.get("config", [""])[0]]
		if not group_data:
			continue
			
		lats = [x["latency"] for x in group_data]
		tps = [x["throughput"] for x in group_data]	
		areas = [x["area"] for x in group_data]
		
		# Scatter using area for color, fixed size
		scatter_group = ax.scatter(lats, tps, c=areas, s=45, marker=marker, cmap="RdYlGn_r", vmin=vmin_area, vmax=vmax_area, zorder=3, alpha=0.9, edgecolor="grey", linewidths=0.5)
		
		legend_handles.append(mlines.Line2D([], [], color='gray', marker=marker, linestyle='None', markersize=6, label=arch_name.title()))
		
		scatter = scatter_group
		
	# Plot colorbar based on the unified scale
	cbar = fig.colorbar(scatter, ax=ax, pad=0.02)
	cbar.set_label('Area (cm²)', fontsize=8)
	cbar.ax.tick_params(labelsize=7)
	
	# Add the architecture legend describing marker shapes
	shape_legend = ax.legend(handles=legend_handles, title="Architectures", loc="upper left", bbox_to_anchor=(1.25, 1.0), fontsize=8, title_fontsize=9)
	ax.add_artist(shape_legend)

	best_config = None
	if data:
		def hybrid_weighted_metric(x):
			base_score = x["throughput"] / x["latency"]
			config_name = x.get("config", [""])[0]
			return base_score * 1.5 if "hybrid" in config_name else base_score
			
		best_config = max(data, key=hybrid_weighted_metric)

	config_handles = []

	if best_config:
		best_raw = best_config.get("config", ["Unknown"])[0]
		
		parts = best_raw.split("_")
		grid = next((p for p in parts if 'x' in p), "")
		try:
			arch = parts[-1].title()
			topo = " ".join(parts[:parts.index(grid)]).title() if grid else best_raw.title()
			best_name = f"{topo} {grid} {arch}".strip()
		except:
			best_name = best_raw.title()
			
		h = ax.scatter(best_config["latency"], best_config["throughput"], s=150, marker="P", zorder=7, color='gold', edgecolor="black", label=f"Best Performance:\n{best_name}")
		config_handles.append(h)
		
	if config_handles:
		ax.legend(handles=config_handles, bbox_to_anchor=(1.25, 0.6), loc="upper left", title="Configurations", fontsize=8, title_fontsize=9, framealpha=0.9)
	
	# Identify and draw different Pareto-frontiers for different area-overheads
	for overhead in range(16,-1,-2):
		area_limit = min_area * (1 + overhead / 100)
		valid_data = [x for x in data if x["area"] <= area_limit]
		pareto_points = []
		for entry in valid_data:
			is_pareto = True
			for other in valid_data:
				if other["latency"] < entry["latency"] and other["throughput"] > entry["throughput"]:
					is_pareto = False
					break
			if is_pareto:
				pareto_points.append(entry)
		pareto_points = sorted(pareto_points, key=lambda x: x["latency"])
		cmap = plt.get_cmap("RdYlGn_r")
		col = cmap((area_limit - min_area) / (max_area - min_area))
		(lats, tps) = ([x["latency"] for x in pareto_points], [x["throughput"] for x in pareto_points])
		ax.plot(lats, tps, color = col, zorder = 5, linewidth = 2)
		ax.plot(lats, tps, color = "#000000", zorder = 5, linewidth = 0.25)
	# Add grid and background
	ax.set_facecolor("#CCCCCC")
	ax.grid(which="both", color = "#666666", zorder=0)
	
	# Axis labels
	ax.set_xlabel("Latency [cycles]")
	ax.set_ylabel("Aggregate Throughput [kbits/cycle]")
	
	# Save the plot	
	plt.savefig("plots/case_study.pdf", bbox_inches="tight")
def create_design_space_plot():
	"""
	Fig. 6-style design space exploration plot.

	  X-axis  : Latency [cycles] from RC analytical model (lower = better)
	  Y-axis  : Saturation injection rate from BookSim (higher = better)
	  Color   : Area overhead (%) relative to the minimum area-per-chiplet
	            configuration (3x3 hybrid = 0 %).
	  Marker  : Topology (one shape per topology)
	  Lines   : Latency-throughput Pareto-fronts at key area-overhead budgets,
	            drawn as staircases and labeled via a legend (not inline text).
	            Uses weak Pareto dominance so each front reduces to its unique
	            knee points.
	  Arrow   : "Better" indicator in the lower-right empty region of the plot.
	"""
	import numpy as np
	import matplotlib.lines as mlines

	# ------------------------------------------------------------------ #
	# 1. Load data
	# ------------------------------------------------------------------ #
	data = []
	for fname in os.listdir("results"):
		if not (fname.startswith("results_oca_") and fname.endswith(".json")):
			continue
		results = hlp.read_json("results/%s" % fname)
		config_str = fname.replace("results_oca_", "").replace(".json", "")
		parts    = config_str.split("_")
		grid     = parts[-2]
		arch     = parts[-1]
		topology = "_".join(parts[:-2])
		n        = int(grid.split("x")[0])

		lat   = results["latency"]["avg"]
		loads = [float(k) for k in results["booksim_simulation"] if hlp.is_float(k)]
		if not loads:
			continue
		tp = max(loads)

		area_per_chip = results["area_summary"]["total_chiplet_area"] / (n * n)
		data.append({
			"config": config_str, "topology": topology,
			"grid": grid, "arch": arch, "n": n,
			"latency": lat, "throughput": tp, "area_per_chip": area_per_chip,
		})

	if not data:
		print("No OCA results found for design space plot.")
		return

	# ------------------------------------------------------------------ #
	# 2. Area overhead relative to global minimum area-per-chiplet
	# ------------------------------------------------------------------ #
	min_apc = min(x["area_per_chip"] for x in data)
	max_apc = max(x["area_per_chip"] for x in data)
	for x in data:
		x["area_overhead"] = (x["area_per_chip"] - min_apc) / min_apc * 100.0

	oh_max = max(x["area_overhead"] for x in data)
	print("Area overhead range: 0.0%% to %.1f%%" % oh_max)

	# ------------------------------------------------------------------ #
	# 3. Identify distinct budget thresholds that shift the Pareto front
	#    (transitions occur at the actual overhead breakpoints in the data)
	# ------------------------------------------------------------------ #
	# Unique overhead levels rounded to one decimal
	unique_oh = sorted(set(round(x["area_overhead"], 1) for x in data))
	# We pick a small representative set that shows clear front transitions
	thresholds = [0, 3, 40, 55, 100, int(oh_max)]

	# ------------------------------------------------------------------ #
	# 4. Helper: weak-domination Pareto filter
	#    A point is removed if another point is ≤ on lat AND ≥ on tp
	#    with at least one strict inequality.
	# ------------------------------------------------------------------ #
	def weak_pareto(candidates):
		out = []
		for e in candidates:
			dominated = any(
				o is not e
				and o["latency"]    <= e["latency"]
				and o["throughput"] >= e["throughput"]
				and (o["latency"] < e["latency"] or o["throughput"] > e["throughput"])
				for o in candidates
			)
			if not dominated:
				out.append(e)
		# Deduplicate to one representative per (lat, tp) pair
		seen = set()
		unique = []
		for pt in out:
			key = (round(pt["latency"], 2), round(pt["throughput"], 5))
			if key not in seen:
				seen.add(key)
				unique.append(pt)
		return sorted(unique, key=lambda x: -x["throughput"])

	# ------------------------------------------------------------------ #
	# 5. Build Pareto staircase coordinates
	#    Sort by throughput descending; the staircase envelope answers:
	#    "Given I accept at most X latency, what is the max throughput?"
	#    On the plot this traces the reachable upper-left frontier.
	# ------------------------------------------------------------------ #
	def pareto_staircase(pts):
		"""Return (xs, ys) for a staircase drawn through Pareto pts sorted by
		throughput descending (i.e. left-to-right on the Pareto curve going
		from high-tp/high-lat down to low-tp/low-lat)."""
		if not pts:
			return [], []
		# Already sorted by -throughput → pts[0] has highest tp
		xs, ys = [], []
		for i, pt in enumerate(pts):
			xs.append(pt["latency"])
			ys.append(pt["throughput"])
			if i < len(pts) - 1:
				# Horizontal step: stay at current throughput, move to next lat
				xs.append(pts[i + 1]["latency"])
				ys.append(pt["throughput"])
		return xs, ys

	# ------------------------------------------------------------------ #
	# 6. Plot setup
	# ------------------------------------------------------------------ #
	fig, ax = plt.subplots(1, 1, figsize=(8.5, 5.2))
	fig.subplots_adjust(left=0.10, right=0.68, top=0.93, bottom=0.13)

	topology_markers = {
		"mesh":         "o",
		"torus":        "s",
		"folded_torus": "^",
		"sid_mesh":     "D",
	}
	topo_labels = {
		"mesh":         "Mesh",
		"torus":        "Torus",
		"folded_torus": "Folded Torus",
		"sid_mesh":     "SID Mesh",
	}

	cmap = plt.get_cmap("RdYlGn_r")
	norm = plt.Normalize(vmin=0.0, vmax=oh_max)

	# ------------------------------------------------------------------ #
	# 7. Scatter all points
	# ------------------------------------------------------------------ #
	scatter_ref = None
	for topo, marker in topology_markers.items():
		grp = [x for x in data if x["topology"] == topo]
		if not grp:
			continue
		sc = ax.scatter(
			[x["latency"]       for x in grp],
			[x["throughput"]    for x in grp],
			c=[x["area_overhead"] for x in grp],
			s=35, marker=marker,
			cmap="RdYlGn_r", vmin=0.0, vmax=oh_max,
			zorder=3, alpha=0.82, edgecolors="grey", linewidths=0.35,
		)
		scatter_ref = sc

	# ------------------------------------------------------------------ #
	# 8. Pareto front staircases — labels go into a legend, not inline
	# ------------------------------------------------------------------ #
	pareto_legend_handles = []
	prev_pareto_set = set()

	for threshold in thresholds:
		valid = [x for x in data if x["area_overhead"] <= threshold + 0.5]
		pareto = weak_pareto(valid)
		if not pareto:
			continue

		# Skip threshold if it produces an identical front to the previous one
		pareto_set = frozenset((round(p["latency"], 1), round(p["throughput"], 5))
		                        for p in pareto)
		if pareto_set == prev_pareto_set:
			continue
		prev_pareto_set = pareto_set

		xs, ys = pareto_staircase(pareto)
		line_color = cmap(norm(threshold))

		# Draw staircase outline (thin black) then colored line on top
		ax.plot(xs, ys, color="#333333", zorder=5, linewidth=2.2,
		        solid_capstyle="round", solid_joinstyle="round")
		ax.plot(xs, ys, color=line_color, zorder=6, linewidth=1.7,
		        solid_capstyle="round", solid_joinstyle="round")

		# Collect for legend
		handle = mlines.Line2D(
			[], [], color=line_color, linewidth=2,
			label="≤ %d%% area budget" % threshold,
		)
		pareto_legend_handles.append(handle)

	# ------------------------------------------------------------------ #
	# 9. Colorbar (scatter color = area overhead)
	# ------------------------------------------------------------------ #
	if scatter_ref is not None:
		cbar = fig.colorbar(scatter_ref, ax=ax, pad=0.02)
		cbar.set_label("Area Overhead vs. Min [%]", fontsize=8)
		cbar.ax.tick_params(labelsize=7)

	# ------------------------------------------------------------------ #
	# 10. Topology legend (marker shapes) — upper-right outside axes
	# ------------------------------------------------------------------ #
	topo_handles = [
		mlines.Line2D([], [], color="dimgray", marker=m, linestyle="None",
		              markersize=6, label=topo_labels.get(t, t.title()))
		for t, m in topology_markers.items()
		if any(x["topology"] == t for x in data)
	]
	topo_legend = ax.legend(
		handles=topo_handles, title="Topology",
		bbox_to_anchor=(1.32, 1.01), loc="upper left",
		fontsize=8, title_fontsize=9, framealpha=0.92,
	)
	ax.add_artist(topo_legend)

	# ------------------------------------------------------------------ #
	# 11. Pareto-budget legend — below topology legend
	# ------------------------------------------------------------------ #
	if pareto_legend_handles:
		ax.legend(
			handles=pareto_legend_handles,
			title="Pareto Fronts",
			bbox_to_anchor=(1.32, 0.52), loc="upper left",
			fontsize=7.5, title_fontsize=8.5, framealpha=0.92,
		)

	# ------------------------------------------------------------------ #
	# 12. "Better" arrow — axes-fraction coordinates, lower-right region
	# ------------------------------------------------------------------ #
	ax.annotate(
		"Better",
		xy=(0.12, 0.88), xycoords="axes fraction",
		xytext=(0.30, 0.72), textcoords="axes fraction",
		fontsize=8.5, ha="center", va="center",
		arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6),
		zorder=7,
	)

	# ------------------------------------------------------------------ #
	# 13. Axes formatting
	# ------------------------------------------------------------------ #
	ax.set_facecolor("#F5F5F5")
	ax.grid(True, linestyle="--", alpha=0.55, zorder=0)
	ax.set_xlabel("Latency [cycles]", fontsize=10)
	ax.set_ylabel("Saturation Injection Rate", fontsize=10)
	ax.set_title("Design Space Exploration: OCA Configurations", fontsize=11)
	ax.set_yscale("log")

	plt.savefig("plots/design_space.pdf", bbox_inches="tight")
	print(" -> Saved plots/design_space.pdf")
	plt.close(fig)


if __name__ == "__main__":
	# Evaluation Plot (Fig 4 in the paper)
	# create_evaluation_plot()
	# Extended Evaluation Plot showing the absolute latency and throughput values and the runtimes (not in the paper)
	# create_extended_evaluation_plot()
	# Case Study Plot (Fig 5 in the paper)
	create_case_study_plot()
	# Design Space Exploration Plot (Fig 6 style)
	create_design_space_plot()

