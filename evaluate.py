"""Run a small fixed question set and write results/results.md (question, tools used, answer, pass/fail)."""
import asyncio, time
from pathlib import Path
from agent import build_agent, tool_calls

CASES = [
    # (question, expected tool, words that must appear, words that must NOT appear)
    ("Which components influence self-consumption?", "kg_influencers", ["battery"], ["heat pump"]),
    ("Which components influence electricity demand?", "kg_influencers", ["heat pump"], ["battery"]),
    ("What are the typical costs of the three solution types?", "kg_sparql", ["12000", "20000", "28000"], []),
    ("What yield does an 8 kWp system get facing south-west (azimuth 225) at 30 degrees tilt?", "estimate_pv_yield_kwh", ["7186"], []),
    ("How much do east-west roofs lose compared to south-facing ones?", "search_knowledge", ["10"], []),
    ("Which components does the heat pump solution consist of?", "kg_neighbors", ["inverter"], []),
]

async def main():
    agent = await build_agent()
    rows, passed = [], 0
    for q, tool, must, must_not in CASES:
        t0 = time.time()
        res = await agent.ainvoke({"messages": [("user", q)]})
        used = [m.name for m in tool_calls(res["messages"])]
        ans = res["messages"][-1].content
        low = ans.lower().replace(",", "")
        ok = (tool in used) and all(w in low for w in must) and not any(w in low for w in must_not)
        passed += ok
        rows.append((q, used, ans.replace("\n", " "), ok, time.time() - t0))
        print(("PASS" if ok else "FAIL"), q)
    out = Path("results"); out.mkdir(exist_ok=True)
    lines = [f"# Evaluation run\n\n{passed}/{len(CASES)} checks passed (automatic keyword + expected-tool check).\n",
             "| # | Question | Tools called | Check | Seconds |", "|---|---|---|---|---|"]
    for i, (q, used, ans, ok, sec) in enumerate(rows, 1):
        lines.append(f"| {i} | {q} | {', '.join(used) or '-'} | {'PASS' if ok else 'FAIL'} | {sec:.0f} |")
    lines.append("\n## Answers\n")
    for i, (q, used, ans, ok, sec) in enumerate(rows, 1):
        lines.append(f"**{i}. {q}**\n\n{ans}\n")
    (out / "results.md").write_text("\n".join(lines))
    print(f"\n{passed}/{len(CASES)} passed -> results/results.md")

if __name__ == "__main__":
    asyncio.run(main())
