# Product

## Register

product

## Users

Two audiences share the same screen:

- **Demo personas** — financial professionals represented by Morgan (trader role, full execute_trade access) and Alex (viewer role, read-only). They use FinFlow to manage a portfolio via natural-language chat.
- **Technical evaluators** — Solo.io prospects, customers, and sales engineers watching the demo. They care about the agent orchestration, policy enforcement, and request tracing happening behind the chat surface.

Both audiences are present simultaneously. The UI must work as a real tool for the persona and as a live showcase for the observer.

## Product Purpose

FinFlow demonstrates Solo.io's agentic platform — agentgateway, agent registry, kagent — via a realistic multi-agent financial portfolio assistant.

The core demo loop: send a chat message, watch three agents (market-data, portfolio, news-sentiment) respond in parallel or one trade-execution agent act, then inspect the Trace and Policies panels to see exactly what happened — which agents ran, how long they took, which policies fired.

Success: an observer can follow the full flow (intent → dispatch → agent → MCP tool → agentgateway routing → policy enforcement → response) without any verbal explanation from the presenter.

## Brand Personality

Precise · Technical · Authoritative.

Voice is direct and dense, like a Bloomberg function reference written by someone who also reads Stripe documentation. No filler. No marketing cadence. Numbers, latencies, and policy states are facts, not features.

Emotional goal: quiet confidence. The system knows what it did and shows you.

## Anti-references

- **Generic SaaS (navy + white)** — corporate blandness, no visual identity, forgettable at a glance.
- **Crypto hype UI (neon chaos)** — too loud, too many competing accents, destroys credibility for financial use.
- **Bloomberg Terminal** — archaic density, 1990s data overload, no visual hierarchy. Inspiration for seriousness only, not aesthetics.
- **Generic AI-created UI** — glassmorphism as default, gradient text, identical card grids, tinted cream/sand backgrounds, hero-metric templates, eyebrow labels on every section. The slop aesthetic that signals no design thought.

## Design Principles

1. **Demonstrate, do not narrate.** Every policy toggle, agent call, and routing decision is visible in the UI. The observer learns by watching, not by being told.
2. **Density earns trust.** Technical information (latency, agent names, policy events, auth flow) is present by default, not hidden behind hover states or drawers. Precision reads as authority.
3. **Control is always visible.** User role, active policies, and system status are legible at a glance. No hidden state.
4. **Demo rhythm first.** The layout guides the presenter: chat → observe right panel → toggle policy → re-run. The spatial flow is the script.
5. **Quiet confidence over flash.** Motion and color serve information, not excitement. A policy block is red because it's blocked, not because red is dramatic.

## Accessibility & Inclusion

Demo context — aesthetics over strict WCAG compliance. Aim for readable contrast on all primary text but do not optimize for edge cases not present in the demo audience.
