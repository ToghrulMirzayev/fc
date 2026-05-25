# Design

This folder holds design source files. Code references these via comments — if you change a token here, update the implementation in the same PR.

## Files

- **`mockup.html`** — full admin console mockup. Single HTML file, opens in any browser. Source of truth for visual decisions through v1.0.

## Design system

The mockup defines the design tokens. They're implemented in two places in the codebase:

- `frontend/tailwind.config.ts` — colors, fonts, sizes, radii
- `frontend/src/app/globals.css` — font import, base styles, shared component classes

Token name conventions (mockup CSS var → Tailwind name):

| Mockup | Tailwind |
|---|---|
| `--bg-deep` | `ink` |
| `--bg-base` | `base` |
| `--bg-elev` | `elev` |
| `--bg-card` | `card` |
| `--text-primary` | `primary` |
| `--text-secondary` | `secondary` |
| `--text-tertiary` | `tertiary` |
| `--text-dim` | `dim` |
| `--accent-coral` | `coral` |
| `--accent-ozone` | `ozone` |
| `--accent-ice` | `ice` |

## Adding a new screen

1. Add the screen mockup to `mockup.html` first.
2. Get the design reviewed before writing the React code.
3. Reuse existing components from `frontend/src/components/` — don't fork them.
4. If you need a new color, radius, or font size, propose it on the mockup first, then add it to `tailwind.config.ts`.

## Logo

The product mark is two angular strokes forming an upward chevron — abstract, decoupled from the "FitnessCourt" working name. Implemented as `<Logo />` and `<LogoMark />` in `frontend/src/components/Logo.tsx`. The mark uses `currentColor` for the outer stroke and fixed coral (`#FF5B49`) for the inner stroke.

To rebrand the wordmark, change `APP_NAME` in `.env`. The mark itself doesn't change.
