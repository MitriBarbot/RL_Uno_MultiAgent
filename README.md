# RL UNO Multi-Agent

Work in progress project exploring **Reinforcement Learning in a multi-agent UNO environment**.

The objective is to build a complete UNO game engine from scratch, create several baseline agents, and progressively train Reinforcement Learning agents able to compete against them.

The project is also designed as an experimentation platform for comparing different decision policies and studying agent behavior.

---

## Current Status

### Implemented

- Custom UNO game engine
- Standard 108-card deck loaded from CSV
- Four-player games
- Turn management
- Reverse direction
- Skip
- Draw Two
- Wild
- Wild Draw Four
- Deck recycling
- Winner detection
- Random starting player
- Legal action detection
- Automated game simulation
- Game statistics
- Unit tests with `pytest`

### Agents

#### RandomAgent

Baseline agent selecting randomly among legal actions.

For Wild cards, the chosen color is random.

#### HeuristicAgent

Simple rule-based baseline.

Current behavior:

- avoids using Wild cards when another legal card is available
- selects randomly among playable colored cards
- chooses the most frequent color in its hand after playing a Wild
- always plays a playable drawn card

This provides a stronger baseline before introducing Reinforcement Learning.

---

## Project Structure

```text
RL_Uno_MultiAgent/
│
├── game.py
├── player.py
├── environment.py
├── benchmark.py
├── requirements.txt
├── README.md
│
├── data/
│   └── data.csv
│
├── agents/
│   ├── base_agent.py
│   ├── random_agent.py
│   ├── heuristic_agent.py
│   └── dqn_agent.py          # WIP
│
├── training/
│   ├── train_dqn.py          # Planned
│   └── train_selfplay.py     # Planned
│
├── evaluation/
│   └── tournament.py         # Planned
│
├── visualization/
│   └── replay.py             # WIP / Planned
│
├── models/
│
└── tests/
    └── test_game.py
```

---

## Game Engine

`UnoGame` contains the core UNO rules and game state.

It handles:

```text
Deck creation
    ↓
Shuffle
    ↓
Deal cards
    ↓
Select starting player
    ↓
Play turns
    ↓
Apply card effects
    ↓
Detect winner
```

The engine is independent from the future Reinforcement Learning implementation.

This allows the same game engine to be used for:

- Random vs Random
- Heuristic vs Random
- DQN vs Random
- DQN vs Heuristic
- future self-play experiments

---

## Benchmarking

The project includes automated simulations for comparing different agents over large numbers of games.

Example experiment:

```text
P1 → HeuristicAgent
P2 → RandomAgent
P3 → HeuristicAgent
P4 → RandomAgent
```

Metrics currently include:

- win rate
- number of turns per game
- execution time

The goal is to establish stable baselines before training RL agents.

---

## Replay / Visualization System

A replay system is currently being developed.

Instead of coupling graphical rendering directly to the game loop, each game will generate structured logs.

A replay contains:

```text
setup
├── initial hands
├── starting card
└── starting player

turns
├── PLAY
├── DRAW
├── PASS
├── PLAY_DRAWN
├── COLOR_CHANGE
├── DIRECTION_CHANGE
└── SKIP

result
├── winner
└── turn count
```

The future visualizer will reconstruct the game exclusively from these events.

This keeps visualization independent from the simulation and allows RL training to run without graphical overhead.

---

## Reinforcement Learning Environment

The next major milestone is the implementation of `UnoEnv`.

`UnoEnv` will act as an adapter between `UnoGame` and the RL agent.

Planned responsibilities:

- fixed observation space
- fixed action space
- legal action masking
- reward calculation
- environment reset
- environment step
- automatic opponent turns

### Planned Observation

The DQN should receive only information legally available to the player, including:

- its own hand
- active card
- active color
- direction
- number of cards held by each opponent

Opponent hands and deck order will remain hidden.

### Planned Action Space

The global action space will contain:

```text
Unique UNO card types
+
Choose Red
Choose Blue
Choose Yellow
Choose Green
+
Draw
Pass
Play Drawn Card
```

An action mask will restrict the available actions depending on the current decision type.

---

## RL Roadmap

```text
UNO Game Engine
      ✅
       ↓
RandomAgent
      ✅
       ↓
HeuristicAgent
      ✅
       ↓
Benchmarks
      ✅
       ↓
Structured Replay Logs
      🚧
       ↓
UnoEnv
      🚧
       ↓
DQN vs Random
       ↓
DQN vs Heuristic
       ↓
Hyperparameter tuning
       ↓
Self-play
       ↓
Multi-agent experiments
```

---

## First DQN Objective

The first learning agent will be trained against three fixed baseline opponents:

```text
DQNAgent
vs
RandomAgent
vs
RandomAgent
vs
RandomAgent
```

Initial reward function:

```text
Win   → +1
Loss  → -1
Else  →  0
```

The environment will initially avoid reward shaping so that the effect of the terminal reward can be evaluated first.

---

## Testing

Run the unit tests with:

```bash
python -m pytest -v
```

The tests currently cover the main game mechanics including:

- legal cards
- player rotation
- reverse
- skip
- Draw Two
- Wild
- Wild Draw Four
- drawing
- deck recycling
- victory conditions
- RandomAgent
- HeuristicAgent

---

## Long-Term Ideas

Possible future experiments include:

- DQN self-play
- historical opponent pools
- multiple learning agents
- PPO comparison
- reward shaping experiments
- policy evaluation against heuristic agents
- tournament system
- interactive replay viewer
- Q-value visualization
- action probability / decision analysis

---

## Motivation

UNO is relatively simple compared with games such as Poker or complex strategy games, but still contains several useful RL challenges:

- hidden information
- stochastic card draws
- multiple opponents
- changing legal action sets
- delayed rewards
- partial observability
- opponent-dependent outcomes

The project is therefore intended as a compact environment for experimenting with Reinforcement Learning concepts while keeping the underlying game understandable and fully controllable.

---

## Status

**Work in Progress**

The classical game engine and baseline agents are functional.

Current development focus:

```text
Structured replay logging
→ visualization
→ RL environment
→ DQN training
```