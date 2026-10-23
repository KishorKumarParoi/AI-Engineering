# ADR 0004: G-Eval Rubric Scoring & Statistical Online A/B Testing

## Status
**ACCEPTED** (Production Deployed)

## Date
2026-10-23

## Context & Problem Statement
Evaluating generative AI systems using simple lexical metrics (BLEU, ROUGE) fails to capture semantic correctness, factual groundedness, or safety adherence. Conversely, relying solely on uncalibrated LLM judges introduces position bias and high variance. Furthermore, deploying pipeline optimizations (e.g. new re-ranking algorithms or tighter guardrail configurations) requires statistically rigorous validation to prove that quality improvements are not random noise.

## Decision
We implement a **Dual Evaluation Framework (Offline G-Eval + Online A/B Testing)**:

1. **G-Eval Methodology (Liu et al., 2023)**:
   - Chain-of-Thought (CoT) based prompt structuring evaluating 4 core dimensions:
     - **Faithfulness / Groundedness** (Weight: 0.35)
     - **Answer Relevance** (Weight: 0.25)
     - **Security & Safety Compliance** (Weight: 0.25)
     - **Technical Precision & Conciseness** (Weight: 0.15)
   - Evaluator generates intermediate step-by-step reasoning before outputting discrete 1-5 rubric scores, normalized to a continuous 0.0 - 1.0 index.
2. **Online A/B Testing Engine**:
   - Session-deterministic 50/50 traffic splitting between `Variant A` (Control) and `Variant B` (Candidate).
   - Automated Welch's t-test hypothesis evaluation:
     $$t = \frac{\bar{X}_1 - \bar{X}_2}{\sqrt{\frac{s_1^2}{N_1} + \frac{s_2^2}{N_2}}}$$
   - Automated p-value calculation determining statistical significance at the $\alpha = 0.05$ threshold.

## Consequences
- **Positive**: Provides reproducible, audit-ready evaluations with mathematical confidence intervals. Automates canary rollout decisions.
- **Negative**: Requires secondary judge LLM tokens during evaluation batches.
