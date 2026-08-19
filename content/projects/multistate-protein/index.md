---
title: Multistate Protein
summary: Studying protein AI across connected biological states through MuSProt, with MusBench for evaluating how models transfer knowledge and remain consistent between states.
aliases:
  - /projects/multistage-protein/
tags:
  - Protein AI
  - AI for Science
  - Benchmarking
links:
  - type: site
    label: MuSProt website
    url: https://huggingface.co/spaces/omaib/MuSProt
---

Protein research spans multiple connected states and representations: understanding and designing proteins requires models to connect sequence, structure, function, interactions, and design. However, most current systems and benchmarks evaluate these problems independently. Strong performance in one state does not necessarily mean that a model can preserve biological constraints, transfer useful information, or support decisions in another.

**MuSProt** is motivated by this gap. It investigates protein AI as a connected multistate problem rather than a collection of isolated prediction tasks. The aim is to understand how knowledge can be transferred between states, how one prediction influences subsequent decisions, and how a model can remain biologically coherent across the complete workflow.

**MusBench** provides the evaluation setting for this research. Beyond measuring performance on individual tasks, it is intended to examine cross-state transfer, consistency, robustness, and error propagation. Together, MuSProt and MusBench aim to make multistate protein modelling measurable and to identify where current protein AI systems succeed or break down.
