# ИНН Чекер — Design Ideas

<response>
<text>
## Idea 1: "Деловой Архив" (Business Archive)
**Design Movement:** Swiss International Typographic Style meets Russian constructivism
**Core Principles:** Grid discipline, typographic hierarchy, functional density, monochromatic restraint
**Color Philosophy:** Near-black (#0F1117) background with off-white (#F5F0E8) text, single accent in deep amber (#D4A853) for active/found states. Red (#C0392B) for liquidated. The amber evokes official stamps and archival documents.
**Layout Paradigm:** Asymmetric split — narrow left column with search + history, wide right panel for results. No centered hero.
**Signature Elements:** Thick left-border rules on section headers, monospace INN/OGRN values in amber, document-style card layout with ruled lines
**Interaction Philosophy:** Instant feedback, no animations except a subtle slide-in for result cards
**Animation:** Result card slides in from right (200ms ease-out), status badge pulses once on load
**Typography System:** IBM Plex Mono for codes, IBM Plex Sans Condensed for labels, IBM Plex Serif for company names
</text>
<probability>0.07</probability>
</response>

<response>
<text>
## Idea 2: "Контрагент" (Counterparty) — Clean Government Data Tool
**Design Movement:** Scandinavian minimalism + data-dense utility UI
**Core Principles:** Clarity over decoration, information hierarchy, generous whitespace, subtle depth
**Color Philosophy:** Crisp white (#FFFFFF) background, slate-900 text, indigo-600 (#4F46E5) as primary action color. Status colors: emerald-600 (active), amber-500 (liquidating/reorganizing), rose-600 (liquidated/bankrupt). Clean, trustworthy, professional.
**Layout Paradigm:** Single-column centered search at top, full-width result card grid below. Search bar is the hero — large, prominent, with INN hint text.
**Signature Elements:** Pill-shaped status badges with colored dot, monospace font for requisite codes, copy-to-clipboard micro-interaction on hover
**Interaction Philosophy:** Every field is copyable; search is instant on Enter; PDF export is one click
**Animation:** Card fades in (300ms), skeleton loading state, copy button flips to checkmark
**Typography System:** Geist Sans for UI, JetBrains Mono for INN/KPP/OGRN values
</text>
<probability>0.08</probability>
</response>

<response>
<text>
## Idea 3: "Реестр" (Registry) — Dark Professional Dashboard
**Design Movement:** Modern SaaS dark dashboard aesthetic
**Core Principles:** Dark surfaces with light content, card-based layout, color-coded status system, data density
**Color Philosophy:** Zinc-950 (#09090B) base, zinc-900 cards, zinc-400 secondary text. Accent: sky-400 (#38BDF8) for interactive elements and found results. Status: green-400/yellow-400/red-400. The dark palette conveys seriousness and professionalism.
**Layout Paradigm:** Full-width dark header with search, results appear as a detailed card below with tabbed sections (Реквизиты / ОКВЭД / Контакты / Налоговая)
**Signature Elements:** Glowing status indicator dot, section dividers with icon+label, gradient top border on active card
**Interaction Philosophy:** Tab-based navigation within result card, smooth transitions between sections
**Animation:** Subtle glow pulse on status dot, tab content crossfade (150ms)
**Typography System:** Outfit for headings, Inter for body, JetBrains Mono for codes
</text>
<probability>0.06</probability>
</response>

## Selected Approach: Idea 2 — "Контрагент"
Clean, professional, data-dense utility UI. Indigo primary, status color system, monospace codes, copy-to-clipboard, PDF export.
