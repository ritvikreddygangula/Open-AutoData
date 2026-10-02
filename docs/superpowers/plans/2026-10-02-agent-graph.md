# Agent Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the five agent nodes into a LangGraph loop that runs SEC chunks end to end and writes `data/trajectories.json` / `data/accepted.json` (plus Snowflake when configured).

**Architecture:** `src/recorder.py` persists one record per round (thread-safe, atomic file writes, optional Snowflake sync). `src/agent_graph.py` builds the StateGraph with pure routing functions and runs chunks in parallel from a CLI.

**Spec:** `docs/PERSON_1_AGENT_ARCHITECT.md` (Instructions for `feat/agent-graph`), `docs/MASTER_SPEC.md` §2-3, Autodata paper Fig. 7.

## Global Constraints
- Order: challenger → verifier → weak solvers → judge(weak) → [weak gate passes] strong solvers → judge(strong) → evaluate → record.
- Any `error`, or verifier `FAIL`, routes straight to evaluate. `REVISE` loops to the challenger; anything else ends.
- Every round is recorded; `ACCEPTED` rounds also go to the accepted set. Snowflake sync only when `snowflake_sync.enabled()`.
- One `run_id` per run; chunks in parallel; one chunk crashing never stops the others.
- Never `git push`; one-line commits.

## Review Focus
1. Two chunks finishing at once → both records survive in the JSON files (lock + atomic replace).
2. Weak gate fails → the strong model is never called.
3. Three failed rounds → graph stops (no recursion-limit crash).
4. Snowflake configured but erroring → pipeline keeps going.
5. An unexpected exception in one chunk → reported for that chunk, others finish.

## Tasks
1. Recorder — tests for append, accepted split, sync calls, sync failures swallowed, concurrent appends. Commit: "Add recorder that writes trajectories, accepted pairs and Snowflake rows".
2. Graph — routing tests + end-to-end fake run (QV fail then accept; weak gate skip; 3-round reject). Commit: "Wire the agent nodes into the LangGraph loop".
3. Runner + CLI — parallel run, crash isolation, summary. Commit: "Add parallel chunk runner and command line entry point".
4. Live run on 1 chunk, code review, changelog.
