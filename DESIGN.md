---
name: FinFlow
description: Multi-agent financial portfolio assistant demonstrating the Solo.io agentic platform.
colors:
  void-base: "#090c12"
  command-surface: "#0d1220"
  data-container: "#101828"
  signal-blue: "#1d8aff"
  confirm-green: "#00e07a"
  deny-red: "#ff4d6a"
  policy-amber: "#f0a500"
  readout-text: "#dde4ed"
typography:
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 800
    letterSpacing: "0.14em"
    lineHeight: 1
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif"
    fontSize: "10px"
    fontWeight: 600
    letterSpacing: "0.06em"
  data:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 800
    lineHeight: 1.1
rounded:
  xs: "2px"
  sm: "3px"
  md: "7px"
  lg: "10px"
  pill: "20px"
  full: "50%"
spacing:
  xs: "6px"
  sm: "9px"
  md: "12px"
  lg: "14px"
  xl: "16px"
components:
  button-send:
    backgroundColor: "{colors.signal-blue}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    size: "34px"
  button-send-hover:
    backgroundColor: "#3a9bff"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    size: "34px"
  button-confirm:
    backgroundColor: "{colors.signal-blue}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "5px 12px"
  toggle-on:
    backgroundColor: "{colors.signal-blue}"
    rounded: "{rounded.pill}"
    width: "34px"
    height: "19px"
  toggle-off:
    backgroundColor: "rgba(255,255,255,0.10)"
    rounded: "{rounded.pill}"
    width: "34px"
    height: "19px"
  agent-tag:
    backgroundColor: "rgba(29,138,255,0.12)"
    textColor: "#6aaeff"
    rounded: "{rounded.sm}"
    padding: "1px 5px"
  ticker-card:
    backgroundColor: "{colors.data-container}"
    textColor: "{colors.readout-text}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm}"
  chat-input:
    backgroundColor: "{colors.data-container}"
    textColor: "{colors.readout-text}"
    rounded: "{rounded.md}"
    padding: "8px 13px"
---

# Design System: FinFlow

## 1. Overview

**Creative North Star: "The Signal Room"**

FinFlow's interface is a signal room: a place where raw data enters, agents process it, and actionable intelligence exits. Everything on screen is infrastructure. The aesthetic is earned, not decorated — dark because the room is focused, dense because the information is real, precise because the operators cannot afford ambiguity. State is always visible. Nothing is hidden behind progressive disclosure unless there is a deliberate reason.

The palette is built on a single saturated accent (Signal Blue, oklch(0.62 0.22 258)) against a three-layer dark carbon stack. Semantic colors — Confirm Green, Deny Red, Policy Amber — are reserved for financial and system state. They are never used decoratively. The result reads less like a SaaS product and more like an instrumented control surface.

This system explicitly rejects generic SaaS (navy + white backgrounds, identical icon-card grids, gradient text), crypto hype (neon chaos, competing accents, glassmorphism), Bloomberg-era density (monochrome overload, no visual hierarchy), and the generic AI aesthetic (cream backgrounds, hero-metric templates, eyebrow labels on every section).

**Key Characteristics:**
- Three-layer depth model: void base → command surface → data container
- One accent color; three semantic state colors — none used decoratively
- System font stack; no display font; labels in uppercase at 10px/600
- Flat surfaces at rest; structural shadow only on overlaid panels (drawer, trace)
- Motion: state transitions only, 200–250ms, cubic-bezier(0.4,0,0.2,1)

## 2. Colors: The Signal Palette

One cold-blue accent on a carbon stack. Semantic state colors do the heavy lifting — they appear only when something has happened.

### Primary
- **Signal Blue** (`#1d8aff`, oklch(0.62 0.22 258)): Interactive elements, active states, current tabs, the logo glyph, send button, policy toggle on-state, agent avatar gradient base. Used on ≤15% of any screen surface.
- **Signal Blue Dim** (`rgba(29,138,255,0.08)`): User chat bubble backgrounds. Transparent overlay of Signal Blue on the void base.
- **Signal Blue Border** (`rgba(29,138,255,0.12)`): All panel and card borders throughout the interface. Consistent at 1px.

### Neutral
- **Void Base** (`#090c12`, oklch(0.08 0.013 254)): The page background. Never used for cards or panels. The darkest layer.
- **Command Surface** (`#0d1220`, oklch(0.11 0.018 254)): Nav bar, panel headers, chat input footer, drawer background. The middle layer.
- **Data Container** (`#101828`, oklch(0.14 0.020 254)): Ticker cards, portfolio card, orders card, chat input field, policy rows. The topmost resting layer.
- **Readout Text** (`#dde4ed`, oklch(0.90 0.013 254)): Primary body text throughout. Never dimmed below `rgba(221,228,237,0.42)` for secondary labels.
- **Muted Text** (`rgba(221,228,237,0.42)`): Secondary labels, panel headers, timestamps, metadata. Minimum contrast usage — labels only, not prose.

### Semantic State
- **Confirm Green** (`#00e07a`, oklch(0.82 0.20 152)): BUY orders, FILLED status, allow verdicts in RBAC, portfolio gains. Financial "up" state.
- **Deny Red** (`#ff4d6a`, oklch(0.65 0.22 12)): SELL orders (label only), RBAC blocked messages, 403 errors, portfolio losses. Financial "down" and system denial.
- **Policy Amber** (`#f0a500`, oklch(0.75 0.17 74)): Policy event traces, enforcement banners, live-effect advisory text in the Policies drawer. Exclusively for agentgateway policy events.

### Named Rules
**The Semantic Firewall Rule.** Confirm Green, Deny Red, and Policy Amber are locked to their semantic roles. A green button is not styled with Confirm Green. An alert that is not about a policy event does not use Policy Amber. If a new use requires one of these colors outside its role, the design is wrong — not the rule.

**The One Accent Rule.** Signal Blue is the only non-semantic accent. It appears on interactive elements, active states, and the logo — not on decorative borders, dividers, backgrounds, or hover states on non-interactive elements.

## 3. Typography

**Display/Title Font:** System UI stack (-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif)
**Body Font:** Same stack — one family throughout.
**Mono/Label Font:** Same stack. Label role uses uppercase + letter-spacing as a visual differentiator, not a separate family.

**Character:** A single well-tuned sans carries everything from the logo to data values to 9px agent tags. No serif, no display face, no decorative pairing. The hierarchy is built entirely through size, weight, and case contrast — not through font variety. This is a control surface; the type should disappear into the information.

### Hierarchy
- **Title / Logo** (800, 14px, letter-spacing 0.14em, uppercase): The FINFLOW wordmark in the nav. Used once — never reused as a section heading.
- **Data Value** (800, 20px, line-height 1.1): Portfolio value dollar amounts. Weight 700 at 14–15px for ticker prices.
- **Body** (400, 13px, line-height 1.5): Chat message content, policy descriptions, trace text. Max line length 65ch in chat bubbles.
- **Label** (600, 10px, letter-spacing 0.06em, uppercase): Panel section headers ("Chat", "Data", "Auth & Routing"), badge/tag text. Used for structural labeling only — four words or fewer.
- **Micro** (600–700, 9px, letter-spacing 0.04em, uppercase): Agent tags (BRIEFING, TRADE, ELICITATION), status badges (FILLED, RBAC BLOCKED). Exclusively for inline state indicators.

### Named Rules
**The Single Family Rule.** One font family throughout. Any design that adds a second family to FinFlow is adding complexity without benefit. Size, weight, and case carry all the hierarchy this system needs.

**The Label Cap Rule.** Uppercase text at 10px or below, only. Body copy in uppercase is prohibited at any size.

## 4. Elevation

FinFlow is flat by default. Cards and panel surfaces carry no shadow at rest. Depth is expressed through the three-layer background stack (void → command → container), tinted 1px borders, and the background step between layers. The user reads depth from color, not from shadow.

The two exceptions are structural: panels that float over the base layout earn a shadow to communicate their stacking position — not as decoration, but as a spatial fact.

### Shadow Vocabulary
- **Drawer Shadow** (`4px 0 28px rgba(0,0,0,0.5)`): The Policies left-drawer only. Indicates it floats above the main content. Applied to the right edge.
- **Trace Shadow** (`0 -4px 24px rgba(0,0,0,0.5)`): The Trace bottom panel only. Indicates it floats above chat and data. Applied to the top edge.
- **Avatar Glow** (`0 0 8px rgba(29,138,255,0.3)`): The FF agent avatar. A low-opacity glow, not a shadow — communicates the avatar is the AI origin point.

### Named Rules
**The Flat-By-Default Rule.** No shadow on cards, ticker cells, input fields, or nav bars. If you are adding `box-shadow` to something that is not an overlay panel, stop. The tinted border (`rgba(29,138,255,0.12)`) provides the definition.

## 5. Components

### Send Button
Circular 34×34px icon button. Signal Blue fill, white arrow icon. No label. 7px radius. On hover: brightens to `#3a9bff`. No border. This is the only full-fill button in the interface. Its distinctiveness communicates primary action.

### Confirm Button (Elicitation)
Text button in Signal Blue fill. "Confirm" label in white, 11px/600. 6px radius, `5px 12px` padding. Used exclusively inside elicitation flows. Same Blue as Send, smaller and labeled — secondary priority.

### Policy Toggle
34×19px pill. On-state: Signal Blue background, white 15×15px knob at `left:17px`. Off-state: `rgba(255,255,255,0.10)` background, white-60% knob at `left:2px`. Transition: `background 0.2s`, `left 0.2s`. No label inside the toggle; external label ("On"/"Off") carries state in green/muted.

### Agent Tag Badge
9px/600 uppercase, letter-spacing 0.04em. `rgba(29,138,255,0.12)` background, 1px `rgba(29,138,255,0.25)` border, `#6aaeff` text, 3px radius, `1px 5px` padding. Values: BRIEFING, TRADE, ELICITATION. Never used for non-agent-routing semantics.

### Ticker Card
Data Container background, 1px Signal Blue Border, 7px radius, 9px padding, center-aligned. Ticker symbol: 9px/700, uppercase, letter-spacing 0.8px, Signal Blue. Price: 14px/700, Readout Text. Change: 10px, Confirm Green for positive, Deny Red for negative. Never use amber or blue for price changes.

### Chat Bubbles
- **User bubble:** `rgba(29,138,255,0.08)` background, 1px `rgba(29,138,255,0.18)` border. Border radius `10px 10px 2px 10px` (flush bottom-right corner faces the avatar position). Right-aligned. Text color `#9ec8f8` (blue-tinted readout, not white).
- **AI bubble:** `rgba(29,138,255,0.06)` background, 1px `rgba(29,138,255,0.14)` border. Border radius `2px 10px 10px 10px` (flush top-left corner faces the avatar). Agent meta line precedes content.

### Policies Drawer
Command Surface background. Slides in from left via `transform: translateX(-100%) → translateX(0)`, 250ms cubic-bezier(0.4,0,0.2,1). 1px Signal Blue Border on right edge. Drawer shadow on right edge. Width 280px. Policy rows use Data Container background, 7px radius. The drawer pushes main content right via `margin-left` on `.content`, not via `z-index` occlusion alone.

### Trace Panel
Absolute-positioned overlay, bottom:0, full width. Expands upward from a 36px collapsed bar. Command Surface background. 1px Signal Blue Border on top edge. Trace shadow on top edge. `height` transition 280ms cubic-bezier(0.4,0,0.2,1). Collapsed bar shows summary line (last intent, agent count, duration). Expanded shows Request Flow column + Auth & Routing column side by side.

### Chat Input
Data Container background, 1px Signal Blue Border, 7px radius, `8px 13px` padding, 13px body text. Placeholder text: Muted Text. No visible focus ring beyond border-color shift. Paired with Send Button in a flex row with `9px` gap.

### Navigation
Command Surface background, 44px height, 1px Signal Blue Border on bottom. Left cluster: Policies button (Data Container bg, bordered, 7px radius) + FINFLOW wordmark (Signal Blue, 800 weight, 2px letter-spacing). Right cluster: agentgateway status dot (Confirm Green, pulsing opacity) + label text. No page navigation links — this is a single-surface application.

## 6. Do's and Don'ts

### Do:
- **Do** use Signal Blue exclusively for interactive elements, active states, and the logo. Its rarity is its authority.
- **Do** express depth through the three-layer background stack. `void-base` → `command-surface` → `data-container` is the only depth vocabulary at rest.
- **Do** use Confirm Green for "allow", "filled", and financial gains. Use Deny Red for "denied", "blocked", and financial losses. Use Policy Amber for agentgateway enforcement events only.
- **Do** keep labels at 10px/600/uppercase and four words or fewer. Structural labels are not headings.
- **Do** keep all panel shadows (`rgba(0,0,0,0.5)`) on the drawer and trace panel only. Everything else is flat.
- **Do** transition state changes at 200–250ms, `cubic-bezier(0.4, 0, 0.2, 1)`. No easing slower than 300ms, no bounce.
- **Do** use the single system font stack throughout. No web fonts, no serif, no mono.
- **Do** include `@media (prefers-reduced-motion: reduce)` for every animated element; substitute an instant transition or opacity crossfade.

### Don't:
- **Don't** use navy + white. Any background lighter than `#090c12` or any dominant white surface breaks the Signal Room aesthetic.
- **Don't** use neon-chaos palettes: multiple competing accents, over-saturated fills, strobing hover effects. Signal Blue is one voice.
- **Don't** replicate Bloomberg-era density: monochrome text walls, no whitespace, undifferentiated information layers.
- **Don't** use generic AI aesthetics: glassmorphism (`backdrop-filter: blur()` used decoratively), gradient text (`background-clip: text`), hero-metric card templates, identical icon-card grids, eyebrow labels on every section.
- **Don't** add `box-shadow` to cards, ticker cells, inputs, or nav bars. Flat-By-Default Rule.
- **Don't** use Confirm Green, Deny Red, or Policy Amber outside their semantic roles. A green button is not an allowed pattern.
- **Don't** add a second font family. One sans throughout.
- **Don't** use uppercase at body sizes (13px or larger). Uppercase is reserved for labels (10px) and micro badges (9px).
- **Don't** animate layout properties (width, height on content areas, margin shifts during scroll). Animate transform and opacity for motion; animate height only on the Trace panel overlay where it is the defining interaction.
- **Don't** use `border-left` greater than 1px as a colored stripe on cards or list items. Full borders, background tints, or nothing.
