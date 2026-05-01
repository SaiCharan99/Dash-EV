# assets/ — Static Files

Served by all three Dash apps. Each app sets `assets_folder` to point to this directory.

## style.css — CSS classes reference

### Layout & cards
- `.dash-card` — subtle lift on hover (`translateY(-1px)` + heavier shadow)
- `.landing-card` — more pronounced lift (`translateY(-5px)`) for landing page product cards

### Navigation
- `.glass-nav` — liquid glass nav bar: `rgba(255,255,255,0.72)` + `backdrop-filter: blur(20px) saturate(180%)` + inset highlight
- `.nav-tabs` — pill tab strip (radio-based); selected pill: white bg + shadow. Used in EV and Energy nav bars.

### Filter controls
- `.seg-control` — segmented radio control (iOS-style); selected segment: white bg + shadow. Used for Season filter.
- `.filter-bar` — flex row wrapping filter controls; collapses to column below 760px.

### Accessibility utilities
- `.skip-link` — keyboard skip-to-content link; visible only on focus
- `.sr-only` — visually hidden but in accessibility tree (1×1px clip)

### Third-party overrides
- `.rc-slider-*` — custom styles for the RangeSlider component (blue track, white handle)
- `.Select-*` — custom styles for the Dropdown component (rounded, Inter font)
- `.modebar` — Plotly modebar hidden globally (`display: none`)

## SVG files
- `lightning.svg` — 20×20 simple bolt icon used in UI (not as cursor)
- `lightning-cursor.svg` — 32×32 gradient bolt (not currently active as cursor)
