---
title: Self-Driving Lab for Metal-Binding Protein Design
summary: An agentic closed-loop laboratory that generates, screens, verifies, and iteratively improves selective and stable metal-binding proteins.
tags:
  - Protein Design
  - Self-Driving Labs
  - Agentic AI
  - AI for Science
links:
  - type: code
    url: https://github.com/wenruifan/MaterialHack-TheSeven
---

Generative models can produce hundreds of candidate metal-binding proteins, but generation alone does not identify which designs will bind the intended metal, reject competing ions, remain structurally stable, and justify the cost of wet-lab synthesis. The central challenge is therefore selection and iterative improvement rather than simply producing more candidates.

This project develops a self-driving laboratory for metal-binding protein design. An agentic loop turns a scientific objective into candidate structures, ranks them with CCDC-informed selectivity and stability filters, verifies their coordination geometry and physical plausibility, records the evidence in durable memory, and uses diagnostic feedback to plan the next design cycle. The goal is to reduce a large generated pool to a small, auditable set of candidates worth experimental validation.
