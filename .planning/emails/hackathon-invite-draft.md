# Quantum Hackathon Invite — Draft Email

**To:** DDSC (Danish Data Science Community), DQC (Danish Quantum Community)
**CC:** Christopher Mohr Jensen, Maxime [Last Name]
**Subject:** Invitation: DDSC × DQC Quantum Portfolio Hackathon — Free Community Event

---

Hi DDSC & DQC teams,

I hope you're both doing well. I'm reaching out with an idea I've been working on that sits right at the intersection of our two communities — and I think it could be a really fun, hands-on experience for our members.

## The Idea: A Quantum Portfolio Optimization Hackathon

I've built a ready-to-go challenge platform where participants solve a real-world **mean-variance portfolio selection problem** formulated as a QUBO (Quadratic Unconstrained Binary Optimization). The task: pick the best 5 assets from a pool of 20 US equities to maximise risk-adjusted returns — using quantum computing, classical methods, or a hybrid approach.

**The best part: it's entirely free and runs on GitHub.**

- Participants fork a repo, submit a JSON solution via pull request, and get scored automatically by GitHub Actions CI/CD — zero infrastructure costs, zero manual intervention.
- Solutions can use **Qiskit**, **PennyLane**, **Cirq**, quantum annealing simulators, or purely classical solvers — everyone is welcome regardless of background.
- A public leaderboard updates in real-time so participants can see where they stand.
- A baseline simulated annealing solver is provided so nobody starts from zero.

The format could work as a **workshop + hackathon at a venue** (e.g. CPH Fintech or similar), with the challenge staying open afterward for async participation. This way we get the energy of an in-person event but the accessibility of an online competition.

## Why DDSC × DQC?

This challenge is designed to bridge quantum computing and data science — exactly what our communities represent. Data scientists get an accessible entry point into quantum optimization, and quantum enthusiasts get to work on a tangible, real-world problem with real market data.

## Advisors & Facilitators

I'd love to bring in some great people to make this event even better:

- **Christopher Mohr Jensen** — I'd like to invite Christopher as an **advisor and facilitator** for the event. His experience and perspective would be invaluable in shaping the hackathon experience and guiding participants.

- **Maxime** — I'd like to invite Maxime to represent the **PennyLane** and **Qiskit** ecosystems. Having someone who can speak to both frameworks would help participants choose the right tools and get unstuck quickly. Maxime's involvement would add real technical depth on the quantum side.

## What's Already Built

The platform is production-ready (Phase 1 complete):
- Frozen challenge instance with validated data (20 tickers, 3 years of daily prices)
- Automated scoring and evaluation pipeline
- Baseline solver for reference
- Comprehensive test suite
- Security-hardened CI/CD architecture (documented pitfalls and mitigations)

Phases 2–4 (automated PR scoring, feedback comments, and live leaderboard) are designed and ready for implementation.

## Next Steps

I'd love to set up a short call or meeting to walk you through the repo, discuss logistics, and figure out the best timing and venue. This is a community initiative — completely free for participants — and I think it could be a fantastic showcase for what DDSC and DQC can do together.

Looking forward to hearing your thoughts!

Warm regards,
[Your Name]
kvantiq.studio

---

*Repository: https://github.com/de-Blanck/ddsc-dqc-portfolio-challenge*
