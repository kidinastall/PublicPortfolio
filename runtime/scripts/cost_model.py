"""Modelled (not billed) input-token cost. Replace with measured numbers from evals/cost."""
V1_PROMPT, V1_PER_TURN = 3000, 250
V5_CONTEXT, V5_CACHED, CACHE_RATE = 3900, 1300, 0.10


def v1_input(turns):
    return sum(V1_PROMPT + V1_PER_TURN * (n - 1) for n in range(1, turns + 1))


def v5_equivalent(turns):
    per_turn = (V5_CONTEXT - V5_CACHED) + V5_CACHED * CACHE_RATE
    return round(turns * per_turn)


if __name__ == "__main__":
    for t in (12, 40):
        a, b = v1_input(t), v5_equivalent(t)
        print(f"{t:>3} turns  v1={a:>7,}  v5={b:>7,}  change={(b - a) / a:+.0%}")
