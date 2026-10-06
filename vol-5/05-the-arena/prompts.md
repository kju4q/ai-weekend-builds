# Prompts: The Arena

This project contains no model and makes no API calls, so unlike the other four
it has no prompts wired into the code. What it has instead is the set of prompts
worth using on your coding assistant while you build it, because an RL project is
unusually easy to get subtly wrong and unusually hard to debug by staring at it.

Use these with Claude Code, Codex, or whatever you build in.

## Prompt 1: Design the state encoding before you write the trainer

This is the prompt that decides whether the project works at all. Run it before
you write a line of `train.py`.

```
I am building a tiny runner game and training a tabular Q-learning agent to play
it, in pure Python, no frameworks. Here is the game's physics:

{paste your constants: jump velocity, gravity, obstacle heights and widths,
spacing, and the jump arc}

Design the discrete state encoding for the Q-table. Requirements:
- Small enough that a few thousand episodes can visit most reachable states
- Rich enough that the optimal action is actually determined by the state
- Every field bucketed, with the bucket boundaries justified against the physics

Tell me the total state space ceiling, your estimate of how many states are
reachable, and which single field I would most regret adding. Do not write the
trainer yet.
```

The last sentence matters. An assistant asked for an encoding will happily hand
you a trainer built on a bad encoding, and you will debug the trainer for an hour.

## Prompt 2: Review the reward function for loopholes

```
Here is the step function and reward for my game:

{paste step()}

Act as an adversarial RL researcher. Find every degenerate strategy that scores
well without playing the game as intended: reward loops, ways to stall, actions
that are free, terminal states that pay better than surviving. For each one, tell
me the smallest change to the environment (not the agent) that closes it.
```

Ask the environment to change, not the agent. Patching an agent to not exploit a
loophole leaves the loophole in your game.

## Prompt 3: Explain a learning curve that looks wrong

The one I actually needed. Paste the real numbers, not a description of them.

```
Tabular Q-learning, 20,000 episodes, epsilon decaying 1.0 to 0.02, alpha 0.2,
gamma 0.99. Reward is +1 per tick survived with a penalty on crash. Here is the
training output:

{paste the episode / epsilon / mean score table}

The mean score climbs to ~1880 by episode 1000 then drops to ~176 by episode
5000 before recovering. Walk me through the candidate explanations in order of
likelihood, and tell me the single cheapest experiment that distinguishes them.
Do not change my hyperparameters yet.
```

For the record, the answer here was exploration, not forgetting, and the cheap
experiment was evaluating the checkpoint greedily with epsilon forced to zero.

## Why "do not write the code yet" earns its place in these prompts

All three prompts above end by withholding the next step. With RL that is worth
being deliberate about, because the failure modes compound: a bad state encoding
produces a trainer that cannot converge, which produces a learning curve you
cannot interpret, which produces hyperparameter changes that are guesses. Asking
for one layer at a time, and confirming it against the physics before moving on,
is the difference between a day of building and a day of flailing.

## Tuning

- **The assistant hands you numpy**: add "standard library only, no numpy, no
  torch, no gym. A plain dict is the Q-table."
- **It writes deep Q-learning instead**: add "tabular only. I want to be able to
  print the policy and read it."
- **The encoding comes back enormous**: add "the total ceiling must be under
  2,000 states. Bucket aggressively and tell me what precision I am giving up."
- **It explains RL at you**: add "I know the algorithm. Answer only the specific
  question about my code."
- **It claims the agent is learning when scores are flat**: add "evaluate with
  epsilon set to 0 before concluding anything, and show me both numbers."

## A note on privacy

Nothing in this project sends anything anywhere. There is no key, no client, no
network call, and the only files written are JSON Q-tables in `output/`. The
prompts on this page are the only place a model is involved, and they go to
whatever assistant you choose to paste them into, carrying your game constants
and your training numbers. If that matters for your project, note that these
prompts never need your training data, only the summary table.
