"""Agentic Semantic Evaluation — sequential agent pipeline for SEMANTIC policy criteria.

This package implements four logical agents that collaborate to evaluate
semantic policy criteria against patient/request evidence.

Flow:
    PolicyAgent → ClinicalEvidenceAgent → EvaluationAgent → Qwen → CriticAgent

Controlled by AgentOrchestrator (sequential, no autonomous loops).
"""
