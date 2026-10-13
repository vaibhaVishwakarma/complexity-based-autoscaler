Scrutiny Report: Verification of Kaggle Training Script Against KD-C Specification

1. Executive Audit Summary and Strategic Context

Adherence to the formalized Knowledge Distillation-Calibration (KD-C) training plan—here specifically applied to the optimization of serverless autoscaling agents—is a strategic necessity for ensuring the reliability of cloud-native architectures. As established in the literature (Agarwal et al., 2023), serverless environments are characterized by high dynamicity and partial observability. Any deviation from the mandated specification—which integrates Adaptive Conformal Inference (ACI) for uncertainty quantification and Deep Recurrent-Reinforcement Learning (LSTM-PPO) for scaling—compromises model reliability. Failure to implement these protocols induces "miscalibration drift" and prevents the agent from managing the sequential dependence of scaling actions, leading to catastrophic "cold start" penalties and degraded system-level performance.

The following table categorizes the five primary discrepancies identified during the audit of the Kaggle training script:

Discrepancy	Criticality	Primary Impact Area
Prediction Set Calibration	Critical	Calibration & Service Level Guarantees
Objective Function Dynamics	High	Throughput & Pareto-Efficiency
Workload Simulation Fidelity	High	Robustness & Real-world Parity
State Observability Modeling	Moderate	Stability & Temporal Robustness
Scaling Action Constraints	Moderate	Resource Efficiency & Exploration Safety

The following technical deep-dive evaluates the specific mathematical and architectural failures of the Kaggle script, contrasting the current non-compliant code with the required standards derived from Agarwal et al. and Gibbs & Candès.

2. Discrepancy 1: Prediction Set Calibration (ACI vs Static Thresholds)

The alignment of prediction sets with actual workload distribution is strategically vital for preserving service reliability. In the context of serverless scaling, the agent must quantify the uncertainty of its execution time and throughput predictions. Static thresholds fail to adapt to distribution shifts, leading to either excessive over-provisioning or critical SLA violations.

The Kaggle script utilizes static, non-adaptive probability estimates for its decision-making. This is a direct violation of the mandated Adaptive Conformal Inference (ACI) protocol defined by Gibbs & Candès (2021). According to their research, default predictors fail to achieve exact marginal coverage in non-stationary environments. Without the ACI update mechanism, the system cannot maintain the target coverage frequency (1-\alpha) required for production-grade reliability.

Mathematical and Systems-Level Consequence The use of static targets induces miscalibration drift. As the workload distribution shifts, the script's failure to update the quantile parameter \alpha_t causes the prediction sets to lose their validity. Specifically, the script fails to implement the update formula: \alpha_{t+1} := \alpha_t + \gamma(\alpha - err_t), where err_t signifies a coverage failure. This results in the agent failing to anticipate demand spikes, directly increasing function instantiation delays (cold starts).

PyTorch-style Code Refactoring To rectify this, the static threshold logic must be replaced with an ACI-based update loop:

# --- REFACTORED: Adaptive Conformal Inference (ACI) Implementation ---
import torch

class ACI_Adjuster:
    def __init__(self, target_alpha=0.1, step_size=0.005):
        self.alpha_t = target_alpha
        self.gamma = step_size # Step size gamma from Gibbs & Candès
        self.target_alpha = target_alpha

    def update(self, covered: bool):
        # Update rule: alpha_{t+1} := alpha_t + gamma * (alpha - err_t)
        err_t = 0 if covered else 1
        self.alpha_t = torch.clamp(
            torch.tensor(self.alpha_t + self.gamma * (self.target_alpha - err_t)),
            0.0, 1.0
        ).item()
        return self.alpha_t


3. Discrepancy 2: Objective Function Dynamics (PPO Clipped Reward vs Static Weights)

In multi-objective serverless environments, dynamic reward balancing is essential for navigating the trade-off between throughput (\phi_t) and resource cost (replica count n_t). Static manual weights are insufficient for the complex variability of FaaS infrastructures.

The Kaggle script employs a basic linear loss without policy stabilization. This contradicts the PPO Clipped Surrogate Objective and the specific reward function r_t formulated by Agarwal et al. (2023). The absence of a clipped objective prevents the agent from achieving a stable Pareto-optimal frontier, as policy updates become overly sensitive to high-variance rewards in the cloud environment.

Mathematical and Systems-Level Consequence The primary risk is gradient dominance by supervised components. Without the L^{CLIP} mechanism (Eq. 1 in Agarwal et al.), the agent experiences training instability. Furthermore, the script's simple reward fails to square the throughput ratio \phi_t^2 and the replica penalty (n_t - n_{min})^2, which are required to penalize sub-optimal configurations aggressively. This leads to a sub-optimal convergence where the model cannot balance CPU/memory utilization (c_t + m_t) against execution time.

PyTorch-style Code Refactoring The reward logic must be updated to comply with the r_t formulation in Agarwal et al.:

# --- REFACTORED: PPO Reward Formulation (Eq. 3, Agarwal et al.) ---
def calculate_reward(phi_t, n_t, n_min, c_t, m_t, is_valid_action, alpha=1.0, beta=1.0, gamma=1.0):
    if not is_valid_action:
        return -100 # r_min for invalid scaling (out of quota N)
    
    # Agarwal et al. Reward: alpha*phi^2 - beta*(n-nmin)^2 + gamma*(c+m)
    reward = (alpha * (phi_t ** 2)) - \
             (beta * ((n_t - n_min) ** 2)) + \
             (gamma * (c_t + m_t))
    return reward


4. Discrepancy 3: Workload Simulation Fidelity (Poisson Sampling vs Static Traces)

The strategic role of aggressive, realistic workload simulation is to prepare the agent for the "wild" traffic patterns of production FaaS. Weak simulation ignores the temporal dependency of bursts and cold starts.

The Kaggle script utilizes constant request rates or simple Gaussian noise. This deviates from the Poisson distribution sampling and Azure Function Trace requirements established by Agarwal et al. (2023) and Schuler et al. (2021). By failing to use production-ready traces (e.g., from the Azure 14-day dataset), the script trains the agent on a simplified Markovian assumption that does not reflect real cloud invocation patterns.

Mathematical and Systems-Level Consequence This results in a catastrophic failure of robustness. When the agent is deployed against real-world "bursty" workloads, its throughput collapses. The 18% throughput improvement and 13% execution time reduction cited in Agarwal et al. are only attainable if the agent learns the non-stationary inter-arrival times of the Poisson process.

PyTorch-style Code Refactoring The workload generation must be refactored to utilize Poisson inter-arrival times:

# --- REFACTORED: Poisson-Based Workload Generation ---
import numpy as np

def generate_workload_requests(lambda_rate, duration=30):
    # lambda_rate derived from Azure Function Trace behavior
    # Requests sampled from Poisson distribution to simulate online behavior
    num_requests = np.random.poisson(lambda_rate * duration)
    return num_requests


5. Discrepancy 4: State Observability Modeling (Missing LSTM Recurrent Units)

Capturing the temporal relationship between scaling actions and their delayed effects on system state is a prerequisite for stability. Traditional RL models struggle with "hysteresis"—the temporal dependency of environment states on past actions.

The audited Kaggle code assumes a fully observable MDP. This is a critical architectural failure; the specification mandates a Partially Observable Markov Decision Process (POMDP) framework utilizing Long Short-Term Memory (LSTM) units. As argued by Agarwal et al. (2023), serverless environments have limited visibility and operational interference, requiring recurrent units to capture the environment parameters (c_t, m_t, \tau_t, \phi_t) as partial observations.

Mathematical and Systems-Level Consequence The consequence is "resource thrashing." Without the internal memory of an LSTM, the agent cannot distinguish between a momentary traffic spike and a sustained workload shift. This leads to oscillating scaling actions, incurring unnecessary cold starts and wasting resources in the cooldown period.

PyTorch-style Code Refactoring The agent must use a RecurrentPPO policy (e.g., from Stable Baselines3) to integrate the LSTM layer:

# --- REFACTORED: LSTM-PPO Policy Integration ---
from sb3_contrib import RecurrentPPO

# MANDATED: Model-free Recurrent RL agent for POMDP
model = RecurrentPPO(
    "MlpLstmPolicy", 
    env, 
    verbose=1,
    policy_kwargs={'lstm_hidden_size': 256, 'n_lstm_layers': 1}
)


6. Discrepancy 5: Scaling Action Constraints (Incomplete Action Masking)

Selective action filtering—preventing the agent from attempting to scale beyond its allocated quota N or below its minimum n_{min}—is essential for training efficiency.

The Kaggle code lacks an Action Masking implementation. It allows the agent to explore "infeasible" actions (e.g., scaling below 1 instance), which merely results in repeated negative rewards r_{min} without meaningful policy improvement. This contradicts the "Action Masking" strategy suggested by Schuler et al. (2021) and Agarwal et al. (2023).

Mathematical and Systems-Level Consequence Failure to mask actions degrades the learning signal. The agent spends significant training capacity exploring invalid state-action pairs, which elongates the training process (exceeding the required 500 episodes) and prevents it from converging on the optimal scaling limits k. This reduces the model’s ability to maximize returns in high-stakes, resource-constrained scenarios.

PyTorch-style Code Refactoring The training loop must apply an action mask based on current replicas n_t and quota N:

# --- REFACTORED: Action Masking for Scaling Limits ---
def get_valid_action_mask(current_replicas, min_replicas, max_quota):
    # Actions: at ∈ {-2, -1, 0, +1, +2}
    actions = [-2, -1, 0, 1, 2]
    mask = []
    for a in actions:
        new_n = current_replicas + a
        mask.append(min_replicas <= new_n <= max_quota)
    return mask # Binary mask to zero out infeasible scaling actions


The cumulative impact of these failures is severe. Without remediation, the model fails to reach the performance benchmarks required for Q1-grade publication in systems/ML literature, particularly the 18% throughput gain and 13% execution time efficiency established in the source context.

7. Final Recommendation and Audit Verdict

Audit Verdict: NON-COMPLIANT

The Kaggle training script is fundamentally non-compliant with the required KD-C/Serverless specification. The current implementation relies on Markovian assumptions and static thresholds that are provably insufficient for partially observable FaaS environments.

Prioritized Remediation Steps:

* Immediate: Implement the LSTM recurrent layer in the PPO policy to transition from a simple MDP to the mandated POMDP framework.
* High Priority: Replace static thresholds with Adaptive Conformal Inference (ACI) to ensure marginal coverage guarantees under distribution shift.
* Medium Priority: Refactor the reward function to include the squared throughput and replica penalty (Agarwal et al., Eq 3) and apply Action Masking.

Conclusion for Peer Review: Without these refactors, the model fails to demonstrate the adaptable policy necessary for production serverless autoscaling. To meet the standards of current ML systems research, the training protocol must be updated to capture temporal dependencies and uncertainty quantification. Failure to do so renders the resulting model ineligible for Q1-level deployment or review.
