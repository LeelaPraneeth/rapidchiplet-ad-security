import matplotlib.pyplot as plt
import helpers as hlp
import os

configs = [
    ("ad_dist", "Distributed Security", "orange", "s"),
    ("ad_shared", "Shared (1 Hub)", "blue", "o"),
    ("ad_shared_2hubs", "Shared (2 Hubs)", "cyan", "^"),
    ("ad_shared_4hubs", "Shared (4 Hubs)", "green", "D")
]

os.makedirs("plots", exist_ok=True)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

areas = []
labels = []
colors = []

for name, label, color, marker in configs:
    res = hlp.read_json(f"results/results_{name}.json")
    
    # Plot Latency vs Load
    keys = sorted([k for k in res["booksim_simulation"].keys() if hlp.is_float(k)], key=float)
    loads = [float(k) for k in keys]
    lats = [res["booksim_simulation"][k]["packet_latency"]["avg"] for k in keys]
    
    ax1.plot(loads, lats, marker=marker, label=label, color=color)
    
    # Area
    area = res["area_summary"]["total_chiplet_area"]
    areas.append(area)
    labels.append(label.replace(" ", "\n"))
    colors.append(color)

ax1.set_xlabel("Injection Load (flits/cycle)")
ax1.set_ylabel("Average Packet Latency (cycles)")
ax1.set_title("Network Saturation Sweep")
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend()

# 2. Area Comparison
ax2.bar(labels, areas, color=colors)
ax2.set_ylabel("Total Silicon Area (mm²)")
ax2.set_title("Physical Area Footprint")
for i, v in enumerate(areas):
    ax2.text(i, v + 0.5, f"{v:.1f} mm²", ha='center', va='bottom')

plt.tight_layout()
plt.savefig("plots/ad_security_evaluation.pdf")
plt.close()
print("Generated comprehensive AD evaluation plots.")
