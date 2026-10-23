# Engineering Case Study: 34.6% Cloud Cost Reduction via Quantized Model Serving

## Author & Architecture Lead
Principal AI Systems Architect

---

## 1. Executive Summary & Problem Context
Serving unquantized 70B parameter models (e.g. Llama-3.3-70B in FP16 / BF16) across enterprise production workloads required 4 x NVIDIA A100 (80GB) or 2 x H100 instances per replica, incurring cloud infrastructure spend exceeding **$9,800 / month per node**.

As query volume scaled beyond 5 million monthly requests, compute expenses threatened product unit economics. The engineering goal was to reduce GPU serving expenditures by **> 30%** while maintaining strictly equivalent response quality (**G-Eval Groundedness degradation < 1.0%** and latency P95 < 2,000ms).

---

## 2. Technical Methodology & Benchmark Experiments
We evaluated three serving architectures across an identical test battery of 1,000 complex enterprise RAG and security evaluation queries:

1. **Baseline**: Llama-3.3-70B in native **FP16** running on 4 x A100 (vLLM engine).
2. **Experiment A (INT8 Weight-Only Quantization)**: BitsAndBytes / SmoothQuant INT8.
3. **Experiment B (AWQ 4-Bit & FP8 TensorRT-LLM)**: Activation-aware Weight Quantization (AWQ) and Hopper FP8 GEMM kernels.

```
Model Architecture Comparison:
-------------------------------------------------------------------------------------
Precision      VRAM Required      Nodes Required      Cost / Hour      P95 Latency
-------------------------------------------------------------------------------------
FP16 (Base)    140 GB             4 x A100 (80GB)     $13.60 / hr      1,820 ms
INT8           75 GB              2 x A100 (80GB)      $6.80 / hr      1,240 ms
AWQ / FP8      42 GB              1 x H100 (80GB)      $4.45 / hr        890 ms
-------------------------------------------------------------------------------------
```

---

## 3. Quality & G-Eval Faithfulness Verification
To prove zero regression in technical accuracy or compliance policy grounding, all outputs were audited via the **G-Eval Continuous Rubric Pipeline**:

| Evaluation Dimension | Baseline (FP16) | INT8 Serving | AWQ / FP8 (Candidate) | Delta vs Baseline |
| :--- | :---: | :---: | :---: | :---: |
| **G-Eval Faithfulness** | 0.914 | 0.912 | **0.911** | - 0.3% (Insignificant) |
| **Answer Relevance** | 0.895 | 0.894 | **0.896** | + 0.1% |
| **Safety & Jailbreak Defense**| 0.998 | 0.998 | **0.998** | 0.0% (Identical) |
| **Technical Precision** | 0.902 | 0.899 | **0.900** | - 0.2% |
| **Mean Quality Index** | **0.927** | **0.926** | **0.926** | **- 0.1% Quality Parity** |

---

## 4. Production Impact & Financial Savings
- **Hardware Footprint Reduction**: Reduced from 4 GPUs per replica to a single H100 GPU per replica.
- **Throughput Increase**: Generation speed increased from 42 tokens/sec to **78 tokens/sec** (+85% higher throughput).
- **Monthly Infrastructure Spend**:
  - Pre-Optimization: **$9,792 / month**
  - Post-Optimization: **$6,408 / month**
  - **Net Reduction: $3,384 / month (34.6% Cost Reduction)**
  - **Annualized Savings: $40,608 / year per serving cluster**.
- **Cold-Start Latency**: Decreased from 180s to **38s** due to 70% smaller container image weights.
