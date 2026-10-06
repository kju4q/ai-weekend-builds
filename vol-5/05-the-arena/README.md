# 05: The Arena

A tiny jumping game you can play yourself, and an agent that learns to play it
better than you by failing at it twenty thousand times. Tabular Q-learning in
plain Python: one dictionary, no frameworks, no numpy, no network calls. You can
read every line that does the learning in about ten minutes.

| Difficulty | Time | Suggested stack |
|---|---|---|
| Advanced | Full day | Python (standard library only) |

## What you'll build

A scrolling terminal runner where blocks come at you and you press space to jump.
Then a trainer that learns the game from nothing but the score, saving checkpoints
as it goes, and a replayer that lets you watch the same agent at any stage of its
training. You will literally watch it go from flailing to untouchable.

The real numbers from a training run on this machine, evaluated on ten tracks the
agent never trained on:

| Checkpoint | Mean score | Survived to the cap |
|---|---:|---|
| ep-00000 (untouched table, coin flips) | 83.4 | 0 of 10 |
| ep-00100 | 77.5 | 0 of 10 |
| ep-01000 | 1716.5 | partly |
| ep-05000 | 1820.7 | partly |
| ep-20000 | 2000.0 | 10 of 10 |

2000 is the evaluation cap, not the agent's ceiling. By twenty thousand episodes
it stops dying, so the only thing that ends an episode is us cutting it off.

## What you'll learn

- **States, actions, rewards**: the three things any RL problem is made of, and
  how to choose them for a game you wrote yourself
- **Why state encoding is the whole job**: 719 reachable states is learnable in a
  minute, a raw pixel grid is not learnable on a laptop at all
- **The Q-learning update**, written once as one line of Python, and what each
  term in it is actually doing
- **Epsilon decay**: why an agent must be forced to do stupid things early on,
  and why that makes its training scores lie to you
- **Reward design**, by getting it wrong on purpose and watching what the agent
  does with the loophole
- **Reading a learning curve honestly**, including the dip that looks like
  failure and is not

## Prerequisites

- Python 3.10+. Nothing to install, not one package.
- A terminal you can press keys in (the human game uses raw keyboard input)
- No API key. Not optional, not needed, not supported. This project has no model
  in it at all, which is rather the point.

## Local vs API

| Part | Runs where |
|---|---|
| The game | 100% local |
| Training the agent | 100% local |
| Replaying checkpoints | 100% local |
| Everything else | 100% local |

Everything, 100% local, no network calls, no key, not even optional. There is no
hosted model anywhere in this project. The intelligence here is 976 dictionary
entries that you generated on your own machine, and you can open the JSON and
read them.

## How it works

```
arena.py            the game. reset() -> state, step(action) -> state, reward, done
   |
   |   state = (dist_bucket, height, width, y_bucket, vy_bucket)      719 reachable
   |   action = 0 do nothing | 1 jump
   |   reward = +1 per tick survived, big penalty on crash
   v
train.py            Q[s][a] <- Q[s][a] + alpha * (reward + gamma * max(Q[s2]) - Q[s][a])
   |                  20,000 episodes, epsilon 1.0 -> 0.02, about 8 seconds
   v
output/ep-*.json    checkpoints at episodes 0, 100, 1000, 5000, 20000
   |
   v
watch.py            replays any checkpoint in the same terminal view you played in
```

## Build it

### Step 1: Play it yourself first

```
python arena.py --play
```

Space to jump, `q` to quit. Play until you can clear a few blocks. This matters:
you need to know what the game feels like before you can judge whether the agent
is good, and you will want a human score to compare against. The tall blocks have
a two-tick takeoff window, so expect to lose.

### Step 2: See the physics written down

```
python arena.py --selftest
```

It prints the actual jump arc, which obstacle heights are clearable from which
takeoff distances, a determinism check, and how many states are reachable. Read
this before training. The timing windows it prints are the entire difficulty of
the game, and they are what the agent has to discover for itself.

### Step 3: Watch a trained agent, before you train one

```
python watch.py --checkpoint sample-data/trained-agent.json --episodes 3
```

This is a finished agent that ships with the repo, so you can see the target
before you spend a minute on training. Then try the pre-trained extremes against
each other:

```
python watch.py --compare output/ep-00000.json output/ep-20000.json --fast
```

### Step 4: Train your own

```
python train.py
```

About eight seconds for twenty thousand episodes. Watch the mean score column.
It will go up, then look like it falls apart around episode 5000, then recover.
Step 6 explains that dip, and it is the most useful thing in this project.

### Step 5: Watch yours learn, stage by stage

```
python watch.py --checkpoint output/ep-00100.json --episodes 2
python watch.py --checkpoint output/ep-01000.json --episodes 2
python watch.py --checkpoint output/ep-20000.json --episodes 2
```

Run them in that order and watch the same agent stop being random. At ep-100 it
jumps at nothing. At ep-1000 it clears the short blocks and dies on the tall
ones. At ep-20000 it does not die.

### Step 6: Break the reward on purpose

```
python train.py --no-crash-penalty
```

Then read "What the agent's failures taught me" below, which is written from what
actually happened when I ran exactly this.

## Verify it works

- [ ] `python arena.py --selftest` prints `selftest ok`
- [ ] `python arena.py --play` renders a lane and responds to the space bar
- [ ] `python train.py` finishes in well under a minute and writes 5 files to `output/`
- [ ] `python watch.py --compare output/ep-00000.json output/ep-20000.json --fast`
      shows the late checkpoint beating the early one by more than 10x
- [ ] `python watch.py --checkpoint sample-data/trained-agent.json --fast --episodes 3`
      scores 2000 on all three
- [ ] The untrained checkpoint survives 0 of 10 tracks and the final one survives 10 of 10

## Why this is the AlphaGo idea at weekend scale

What is genuinely the same idea:

- The agent is never told how to play. No rules about jump timing, no examples of
  good play, no human games to imitate. It gets a score and nothing else.
- It learns a value estimate: a guess at how much future reward each move is
  worth from each situation, and it improves that guess from its own experience.
- The learning rule is the same family. The one line in `train.py` is temporal
  difference learning, the same foundation underneath the famous results.
- Exploration is forced early and withdrawn later, because an agent that only
  does what currently looks best never discovers anything better.

What is emphatically **not** the same, and it is most of the engineering:

- **No neural network.** A dictionary with 976 entries, one per situation it has
  met. AlphaGo learned a representation of positions it had never seen; this
  agent looks situations up in a table and knows nothing about any state missing
  from it.
- **No self-play.** The game does not adapt. There is no opponent getting better
  as the agent does, which is the mechanism that made AlphaGo's training
  interesting.
- **No search.** AlphaGo thought ahead with Monte Carlo tree search at move time.
  This agent does a dictionary lookup and jumps or does not.
- **A hand-built state encoding.** I chose the five numbers that describe a
  situation, and I bucketed them so the table stays small. Choosing that
  encoding by hand is exactly the work deep RL exists to avoid.

So: same core loop, none of the machinery that makes the core loop scale. Which
is a fine thing to understand in an evening, as long as nobody tells you that you
just rebuilt AlphaGo.

## What the agent's failures taught me about my own game

This is the section worth your time. Every item below is something I observed
while tuning this, not a general lesson I looked up.

**Early training is worse than random, and that is not a bug.** The untouched
table scores 83.4 because a coin flip occasionally jumps at the right moment. At
episode 100 it scores 77.5, measurably *worse*. It has learned just enough to
have opinions and all of them are wrong. If I had judged the approach at episode
100 I would have thrown it away.

**The training curve is not the skill curve, and mine lied to me.** My training
output showed mean score climbing to about 1880 by episode 1000 and then
collapsing to 176 by episode 5000. It looks like catastrophic forgetting. It is
not. At episode 5000 epsilon is still 0.59, so the agent is being forced to act
randomly on nearly six of every ten ticks, and random jumps in this game are
fatal. Evaluated greedily, with exploration switched off, that same episode-5000
table scores **1820.7**. It had not got worse at all; I was watching a
handicapped version of a competent agent. Always evaluate greedily before you
conclude anything about a dip.

**My crash penalty turned out to be redundant, and the agent proved it.** I added
a large negative reward for crashing because it seemed obviously necessary.
Training with `--no-crash-penalty` reaches a mean of 1967.7, which is roughly the
same place. The reason is that reward is +1 per tick survived and crashing ends
the episode, so dying already costs the agent every point it would have earned
for the rest of the run. The penalty was me paying twice for the same lesson.
When a reward signal already has a natural terminal cost, extra punishment is
decoration. I kept it on by default because it converges slightly earlier, not
because the agent needs it.

**The game design, not the algorithm, decided whether learning was possible.**
Two choices I made while building the game turned out to matter far more than any
hyperparameter. `GAP_MIN = 9` means the tightest block spacing forces the player
to land and immediately jump again, so spamming jump cannot work. The selftest
confirms the baseline: always-jump scores 94.0, barely better than random. And
bucketing distance at 13 values instead of tracking it exactly is what keeps the
table at 719 reachable states instead of tens of thousands. Had I left distance
unbucketed, twenty thousand episodes would not have been close to enough, and I
would probably have blamed Q-learning.

**Height 10 at width 2 has exactly one correct answer, and the agent found it.**
The arc only clears a 10-high block on ticks 4 and 5, and a 2-wide block needs
two consecutive clearing ticks, so there is precisely one takeoff distance that
works. I did not know that when I wrote the constants; I worked it out afterwards
to explain why the agent kept dying there. The agent found that single pixel of a
solution before I understood that it was single. That is the thing about reward:
you do not have to understand your own game for the agent to solve it, which also
means the agent is not going to tell you when your game is unfair.

## Extend it

- Add a duck action and low-hanging obstacles, then see how much bigger the state
  space gets and how much longer training takes
- Log the policy: for each distance bucket, print whether the agent jumps. You
  get a readable strategy table out of a trained agent, which you cannot do with
  a neural network
- Make the game adaptive (speed up as the score climbs) and watch a table trained
  on the easy version fail on the hard one
- Swap Q-learning for SARSA and compare. Two small changes, measurably different
  risk appetite
- Add a second obstacle to the state so the agent can plan two blocks ahead
- Train against a human replay: record your own games and see whether your score
  beats ep-01000 (it probably will) or ep-20000 (it probably will not)

## Common pitfalls

- **Judging it too early**: at episode 100 the agent is worse than random. Train
  the full run before deciding anything.
- **Reading the training mean as skill**: it is depressed by forced exploration.
  Use `watch.py` on a checkpoint to see the real policy.
- **Making the state space too rich**: add one unbucketed continuous value and
  the table stops converging. Every new state is a thing it must fail at
  separately.
- **Terminal input**: the human game puts your terminal into raw mode. If a crash
  leaves it strange, run `reset`. Running `--play` in a non-interactive shell will
  not work, which is why `--demo` and `--fast` exist.
- **Expecting the checkpoints to be comparable across runs**: training is
  stochastic. Your ep-05000 will not match mine. The shape of the curve will.

## Made by

[@qendresahhoti](https://instagram.com/qendresahhoti) on Instagram, [@qbuilder](https://tiktok.com/@qbuilder) on TikTok.
