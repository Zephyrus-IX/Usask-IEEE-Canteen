# Usask IEEE Canteen design system

Source reference: AI-generated mockup provided 2026-09-08.

## Visual direction

- Branded IEEE dashboard with a dark blue technology frame, light airy content area, circuit-line decoration, and a McNaughton Centre hero illustration.
- The design should feel like an IEEE student branch kiosk/POS tool: institutional, clean, fast, and touch-friendly.
- Keep cashier workflows practical; this styling is the shell and navigation layer, not a reason to slow down sale entry.

## Palette

| Token | Value | Use |
| --- | --- | --- |
| `--ieee-navy` | `#062454` | Header/footer frame, primary text contrast |
| `--ieee-blue` | `#005baa` | IEEE blue, icons, links, primary controls |
| `--ieee-cyan` | `#0097dc` | Active states, accent bars, circuit lines |
| `--ieee-sky` | `#8fc9f4` | Mobile arrows, light decorative waves |
| `--ieee-ice` | `#edf8ff` | Panels, table headers, message boxes |
| `--ieee-ink` | `#071947` | Main headings and body text |

## Layout

### Desktop

- Rounded app shell centered on the page with a dark blue top bar and bottom wave/footer.
- Header contains IEEE lockup, CANTEEN wordmark, and horizontal nav.
- Hero uses a two-column layout: left text, right McNaughton-style building illustration.
- Dashboard cards use a 3-column grid with large icons and circular arrow buttons.
- Primary `New Sale` card is a blue gradient; secondary cards are frosted white.

### Mobile

- Full-bleed shell with compact top bar.
- Header hides the full nav and shows a hamburger affordance.
- Hero compresses into title/subtitle plus a shorter building illustration.
- Dashboard cards become stacked touch rows with icon, copy, and right arrow.
- Footer keeps IEEE mark and location only.

## Components

- **IEEE mark:** CSS diamond plus inline text approximation. Replace with official branch-approved vector/logo if available.
- **Hero art:** lightweight inline SVG approximation of McNaughton Centre. Replace with an approved image or commissioned vector if exact likeness matters.
- **Circuit pattern:** repeated SVG data URI in CSS for header, cards, and footer.
- **Navigation card:** icon, title, short description, arrow affordance. Use the same structure for all dashboard destinations.

## Asset TODOs

1. Add official IEEE Student Branch logo/wordmark if the branch has a usable SVG/PNG.
2. Replace generated building art with either:
   - an approved photo with watercolor/illustration treatment, or
   - a hand-created SVG/illustration based on an approved reference.
3. Confirm whether `Load Balance` stays as its own dashboard card or is nested under `Student Tabs` later.
