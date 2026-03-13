# RapidChiplet — Chiplet Security Evaluation

Chiplet network architecture evaluation for **security** use cases, built on top of the [RapidChiplet](https://github.com/spcl/rapidchiplet) simulation framework.

This repository extends RapidChiplet with:
- **Security-focused chiplet architectures** (distributed, shared hub, hybrid security models)
- **Large-scale design-space sweep** across 4 topologies × 8 grid sizes × 3 architectures
- **Two publication-quality plots** reproduced from pre-computed results

---

## Dependency

This project is built on top of [RapidChiplet (spcl/rapidchiplet)](https://github.com/spcl/rapidchiplet).
The core simulation engine (`rapidchiplet.py`), utilities (`helpers.py`, `global_config.py`), and BookSim2 wrapper are sourced from that project. To track upstream changes:

```bash
git remote add upstream https://github.com/spcl/rapidchiplet.git
git fetch upstream
```

---

## Plots

| Plot | Script | Description |
|------|--------|-------------|
| `plots/case_study.pdf` | `create_paper_plots.py` | Design-space scatter: latency vs throughput across all configurations (3x3 SID-Mesh hybrid wins) |
| `plots/ad_security_evaluation.pdf` | `plot_ad_comparison.py` | Latency-load curves + area comparison for 4 security architectures |

---

## Quick Start — Regenerate the Plots

Results are pre-computed and included in `results/`. To regenerate the plots:

```bash
pip install -r requirements.txt

# Case study scatter plot
python3 create_paper_plots.py

# Security architecture evaluation
python3 plot_ad_comparison.py
```

Output PDFs are saved to `plots/`.

---

## Repository Structure

```
.
├── create_paper_plots.py      # Generates plots/case_study.pdf
├── plot_ad_comparison.py      # Generates plots/ad_security_evaluation.pdf
├── run_extensive_sweep.py     # Runs the full design-space sweep (regenerates results/results_oca_*.json)
├── generate_ad_configs.py     # Generates BookSim config for security simulations
├── generate_ad_designs.py     # Generates chiplet placements/topologies for security architectures
├── generate_ad_traffic.py     # Generates traffic patterns for security chiplets
├── run_ad_simulations.py      # Runs security simulations (regenerates results/results_ad_*.json)
│
├── rapidchiplet.py            # Core RapidChiplet simulator (from spcl/rapidchiplet)
├── helpers.py                 # JSON I/O and graph utilities
├── global_config.py           # Color palette definitions
├── booksim_wrapper.py         # Interface to BookSim2 cycle-accurate simulator
├── generate_topology.py       # Network topology generators (mesh, torus, etc.)
├── generate_routing.py        # Routing table generation (SPLIF algorithm)
├── generate_placement.py      # Chiplet placement generation
├── generate_traffic.py        # Synthetic traffic pattern generation
├── validation.py              # Input validation
├── routing_utils.py           # Routing utilities
├── run_experiment.py          # Automated design space exploration runner
│
├── results/
│   ├── results_oca_*.json     # Pre-computed sweep results (96 configs × topologies)
│   └── results_ad_*.json      # Pre-computed security architecture results (4 variants)
│
├── plots/
│   ├── case_study.pdf         # Design-space scatter plot
│   └── ad_security_evaluation.pdf  # Security latency + area comparison
│
├── inputs/
│   ├── designs/               # Design spec files (chiplets + placement + topology + routing)
│   ├── chiplets/              # Chiplet catalog (shared, distributed, hybrid variants)
│   ├── technologies/          # Technology node parameters (32nm)
│   ├── packagings/            # Interposer/packaging configurations
│   ├── booksim_configs/       # BookSim sweep parameters
│   ├── placements/            # Chiplet placement files
│   ├── topologies/            # Network topology definitions
│   ├── routing_tables/        # Pre-generated routing tables
│   └── traffic_by_chiplet/    # Traffic pattern files
│
├── experiments/               # Experiment configuration files
├── booksim2/                  # BookSim2 submodule (cycle-accurate NoC simulator)
└── requirements.txt
```

---

## Reproducing Results from Scratch

### Design-Space Sweep

Regenerates all simulation results used in `case_study.pdf`:

```bash
python3 run_extensive_sweep.py
```

This sweeps:
- **Topologies**: mesh, torus, folded_torus, sid_mesh
- **Grid sizes**: 3×3, 4×4, 5×5, 6×6, 8×8, 10×10, 12×12, 16×16
- **Architectures**: shared, distributed, hybrid

Results are saved to `results/results_oca_<topology>_<grid>_<arch>.json`.

### Security Architecture Simulations

Regenerates the 4 security architecture results used in `ad_security_evaluation.pdf`:

```bash
python3 generate_ad_configs.py
python3 generate_ad_designs.py
python3 generate_ad_traffic.py
python3 run_ad_simulations.py
```

Architectures evaluated:
- **Distributed** — each chiplet has its own security module
- **Shared (1 hub)** — single centralized security hub
- **Shared (2 hubs)** — two security hubs
- **Shared (4 hubs)** — four security hubs

---

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Build BookSim2

```bash
cd booksim2/src
make
cd ../../
```

### 3. (Optional) Build Netrace for trace-driven simulation

```bash
cd netrace
gcc export_trace.c netrace.c -o export_trace
cd ../
```

---

## Key Results

### Case Study (`case_study.pdf`)
Scatter plot across all topology/grid/architecture combinations.
- X-axis: Latency (cycles)
- Y-axis: Aggregate Throughput (kbits/cycle)
- Color: Physical silicon area (cm²)
- Marker shape: Architecture type (○ shared, □ distributed, ◇ hybrid)
- **Best configuration: 3×3 SID-Mesh Hybrid** (gold star ✦)

### Security Evaluation (`ad_security_evaluation.pdf`)
Comparison of 4 security architectures under increasing injection load.
- Left: Average packet latency vs. injection load (network saturation sweep)
- Right: Total silicon area footprint per architecture

---

## References

- RapidChiplet paper and simulator: https://github.com/spcl/rapidchiplet
- BookSim2 cycle-accurate NoC simulator: https://github.com/booksim/booksim2
- Netrace trace-driven simulation: https://github.com/booksim/netrace
