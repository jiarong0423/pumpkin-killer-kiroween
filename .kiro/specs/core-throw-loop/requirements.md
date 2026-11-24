# Requirements: Core throw loop

## Introduction

One round of play: every living unit chooses an angle and charge, the engine
resolves all throws, wind changes, the next round starts. Humans and
sub-agents use the same MCP tools.

## Requirements

### 1. Submit a throw

**User story:** As a player, I want to set an angle, hold to charge and release,
so that my throw resolves right away and I can correct on the next round.

1. WHEN a unit submits an angle between 0 and 90 degrees and a charge between
   0 and 100 percent, THEN the system SHALL record exactly one throw for that
   unit in the current round.
2. IF a unit submits a second throw in the same round, THEN the system SHALL
   reject it and keep the first.
3. IF the round timer expires before a unit submits, THEN the system SHALL
   mark that unit as idle for the round.

### 2. Resolve a round

**User story:** As a player, I want the human side and the sub-agent side to
take alternating phases, so that I can read the agents' landing points and
correct my next throw.

1. WHEN every living human unit has submitted or timed out, THEN the system
   SHALL resolve the human phase using the round's wind and a published aim
   error, then open the sub-agent phase.
2. WHEN every living sub-agent unit has submitted or timed out, THEN the
   system SHALL resolve the sub-agent phase, then start the next round.
3. THE system SHALL reveal landing points of a phase only after that phase
   resolves, and sub-agents SHALL see the human phase's landing points.
4. WHEN a unit's hit points reach zero, THEN the system SHALL remove it from
   later phases.

### 3. Public state only

**User story:** As a sub-agent opponent, I want the same public information a
human sees, so that the contest is fair.

1. THE system SHALL expose positions, hit points, current wind and past
   landing points through `get_public_state`.
2. THE system SHALL NOT expose other units' unsubmitted choices, future wind
   or the random seed through any tool.
3. WHEN a client requests state for a room it has not joined, THEN the system
   SHALL reject the request.

### 4. No shortcuts for the AI

**User story:** As a human player, I want the AI to improve only from the
public record, so that a win or a loss means something.

1. THE system SHALL NOT provide any tool that predicts a trajectory or
   simulates a throw to any client or sub-agent.
2. THE system SHALL expose past landing points, each with its angle, charge
   and wind, as the only learning data for sub-agents.
3. WHEN a sub-agent submits a throw, THEN the system SHALL apply the same
   published aim error as for human units.

### 5. Determinism

1. GIVEN the same seed and the same submitted throws, THE system SHALL produce
   the same round result.
