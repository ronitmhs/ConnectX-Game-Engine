# ConnectX Game Engine

A high-performance Connect Four game engine developed for the Kaggle ConnectX competition.

## Goals

- Build a competitive Connect Four engine using adversarial search
- Optimize performance under Kaggle's 2-second move limit
- Analyze real competition episodes to identify failure modes
- Target a Kaggle rating of 1150-1190

## Planned Engine Features

- Bitboard board representation
- Iterative deepening
- Negamax / alpha-beta search
- Transposition tables
- Tactical threat and fork detection
- Gravity-aware evaluation
- Opening book
- Time management
- Automated tournaments and regression testing

## Data Analysis

Real Kaggle competition episodes are used for:

- Win/loss analysis
- First-player vs. second-player performance
- Move and opening analysis
- Failure-mode detection
- Engine regression testing
- Experimental evaluation of engine changes

## Current Baseline

V4 uses iterative-deepening alpha-beta search with heuristic board evaluation and serves as the baseline for future engine versions.
