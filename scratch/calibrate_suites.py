"""
calibrate_suites.py — Calibrate all suite YAML configs to match Gate 2 profiling & eliminate bottlenecks.

Calibrated Service Times:
- EdgePreprocess:    0.002s (mu = 500 RPS)
- EdgeInference:     0.003s (mu = 333 RPS)
- CloudRefineWorker: 0.0625s (mu = 16.0 RPS/worker, grounded in Gate 2 Tesla T4 profile)
- Sink:              0.001s (mu = 1000 RPS)
"""

from pathlib import Path
import yaml
from continuum_ext.workload.conformal_workloads import (
    REGIME_INITIALIZATION_PROFILES,
    get_regime_initialization
)

SUITES_DIR = Path("configs/suites")
SUITES_DIR.mkdir(parents=True, exist_ok=True)

# Base template based on preliminary_multinode_split_inference.yaml
BASE_YAML = """scenario: split_inference
realism_tier: T0
step_seconds: 1.0
infrastructure:
  infrastructure_id: multinode_continuum_infra
  n_space: 0
  n_iot: 4
  n_edge: 8
  n_cloud: 6
  cloud:
    cpu: 24.0
    ram: 48.0
    storage: 1000.0
  iot_to_edge:
    latency: 5.0
    bandwidth: 1000.0
  edge_to_cloud:
    latency: 25.0
    bandwidth: 1000.0
stages:
  CameraSource:
    priority_prob_high: 0.5
    output_size_bytes: 200000
    processing_time_s: 0.0
    resources:
      placement_layers:
      - iot
  EdgePreprocess:
    processing_time_s: 0.002
    resources:
      placement_layers:
      - edge
  EdgeInference:
    processing_time_s: 0.003
    triage_high_priorities:
    - critical
    - high
    resources:
      placement_layers:
      - edge
  CloudRefineWorker:
    processing_time_s: 0.0625
    resources:
      placement_layers:
      - cloud
  Sink:
    processing_time_s: 0.001
    deadline_s: 15.0
    resources:
      placement_layers:
      - edge
autoscaling:
  hpa:
    target_utilization: 0.7
    tolerance: 0.1
    min_replicas: 1
    cooldown_epochs: 2
  keda:
    queue_target_per_worker: 6
    activation_queue_length: 2
    min_replicas: 1
    cooldown_epochs: 2
  inferline:
    alpha_fast: 0.6
    alpha_mid: 0.2
    alpha_slow: 0.05
    stabilise_epochs: 10
    safety_margin: 1.15
    min_replicas: 1
    cooldown_epochs: 2
  complexity_blind:
    alpha: 0.3
    assumed_fp: 0.5
    safety_margin: 1.2
    min_replicas: 1
    cooldown_epochs: 2
  conformal:
    fp_preempt_threshold: 0.35
    fp_recovery_threshold: 0.45
    set_size_recovery_max: 1.8
    alpha_lambda: 0.35
    safety_margin: 1.2
    min_replicas: 1
    cooldown_epochs: 2
placement:
  strategy: best_fit
  place_every_epochs: 2
"""

REGIMES = [
    # Suite 1
    ("suite1_flat", 60, 15),
    ("suite1_spike", 80, 15),
    ("suite1_burst", 80, 15),
    ("suite1_ramp", 120, 15),
    ("suite1_zero_begin", 70, 15),
    ("suite1_zero_terminal", 165, 15),
    # Suite 2
    ("suite2_shock", 90, 15),
    ("suite2_recovery", 120, 15),
    ("suite2_compound_stress", 120, 15),
    ("suite2_compound_relief", 120, 15),
    ("suite2_decoupled_opposing", 120, 15),
    ("suite2_opposing1", 120, 15),  # backward compat
    ("suite2_opposing2", 120, 15),  # backward compat
    ("suite2_storm", 90, 15),
    # Suite 3
    ("suite3_azure", 120, 15),
]

for regime_name, epochs, drain_epochs in REGIMES:
    cfg = yaml.safe_load(BASE_YAML)
    init_profile = get_regime_initialization(regime_name)

    cfg["scenario_config"] = {"application_id": f"SplitInference_{regime_name}"}
    cfg["epochs"] = epochs
    cfg["drain_epochs"] = drain_epochs
    cfg["workload"] = {"streams": {"CameraSource": {"generator": regime_name}}}

    min_w = init_profile.get("min_workers", 1)
    init_w = init_profile.get("initial_workers", 2)
    max_w = 18

    if regime_name == "suite3_azure":
        cfg["workload"]["streams"]["CameraSource"]["rate_scale_factor"] = 0.08

    cfg["scaling"] = {
        "pools": {
            "CloudRefine": {
                "min_workers": min_w,
                "initial_workers": init_w,
                "max_workers": max_w,
                "startup_delay_s": 1.0,
            }
        },
        "queue_up_threshold": 8,
        "queue_down_threshold": 2,
    }

    # Autoscaler min_replicas floor matching regime
    for ctrl in ["hpa", "keda", "inferline", "complexity_blind", "conformal"]:
        if ctrl in cfg.get("autoscaling", {}):
            cfg["autoscaling"][ctrl]["min_replicas"] = min_w

    out_file = SUITES_DIR / f"{regime_name}.yaml"
    with open(out_file, "w") as f:
        yaml.dump(cfg, f, sort_keys=False, default_flow_style=False)
    print(f"Generated {out_file}: epochs={epochs}, init_w={init_w}, min_w={min_w}, max_w={max_w}")

print("Successfully calibrated and generated all suite YAML configurations!")
