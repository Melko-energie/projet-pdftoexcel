# Design System Document: Precision Editorial

## 1. Overview & Creative North Star
**The Creative North Star: "The Architectural Ledger"**

This design system moves beyond the utility of a standard SaaS tool and enters the realm of a high-end financial publication. For a B2B tax data extraction tool, "clean and functional" is the baseline—our goal is **Authority through Negative Space.** 

We reject the "boxed-in" look of traditional software. Instead, we embrace **Architectural Layering**: using light, shadow, and tonal shifts to define structure. The aesthetic is inspired by premium editorial design—generous margins, sophisticated typography scales, and a "No-Line" philosophy that makes complex tax data feel breathable, manageable, and indisputably accurate.

---

## 2. Colors: Tonal Depth over Borders
Our palette is rooted in a spectrum of professional blues and atmospheric greys. We prioritize cognitive ease by reducing visual noise.

### The "No-Line" Rule
**Prohibit 1px solid borders for sectioning.** To separate a sidebar from a main content area, do not draw a line. Instead, shift the background from `surface` (#f8f9fa) to `surface-container-low` (#f3f4f5). Boundaries are felt through tonal transitions, not seen through rigid strokes.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. Use the following tiers to create "nested" depth:
*   **Base Layer:** `surface` (#f8f9fa) – The infinite canvas.
*   **Sectional Layer:** `surface-container-low` (#f3f4f5) – Use for large secondary areas like sidebars or secondary panels.
*   **Content Cards:** `surface-container-lowest` (#ffffff) – Reserved for the highest priority data containers to make them "pop" against the grey base.
*   **Interaction Layer:** `surface-container-high` (#e7e8e9) – For hovered states or active utility panels.

### The "Glass & Gradient" Rule
To elevate the "PDF Table Extractor" above generic competitors:
*   **Floating Modals:** Use `surface_container_lowest` at 80% opacity with a `20px` backdrop blur.
*   **Signature Textures:** For primary CTAs and Progress Bars, use a subtle linear gradient from `primary` (#003461) to `primary_container` (#004b87). This adds a "lithographic" depth that flat hex codes lack.

---

## 3. Typography: The Editorial Scale
We utilize a dual-font strategy to balance character with clinical precision.

*   **Display & Headlines (Manrope):** A modern geometric sans-serif with a high x-height. Use `display-lg` through `headline-sm` for high-level metrics and page titles. It signals a "premium" brand voice.
*   **Data & UI (Inter):** A highly legible workhorse. Use `title-md` down to `label-sm` for all extracted data, table headers, and functional UI elements. 

**Hierarchy as Wayfinding:**
*   **Extracted Values:** Use `title-lg` (Inter) in `on_surface` (#191c1d) to ensure tax figures are the focal point.
*   **Metadata:** Use `label-md` (Inter) in `on_surface_variant` (#424750) for timestamps and file names.

---

## 4. Elevation & Depth: Tonal Layering
Traditional shadows are often "muddy." In this system, depth is clean and architectural.

*   **The Layering Principle:** Place a `surface-container-lowest` card on a `surface-container-low` background. The slight shift from #ffffff to #f3f4f5 creates a natural lift.
*   **Ambient Shadows:** For floating elements (e.g., a file preview), use a "tinted shadow." Instead of grey, use `on_surface` at 5% opacity with a `32px` blur and `8px` Y-offset. This mimics natural light passing through a high-end workspace.
*   **The "Ghost Border" Fallback:** If a border is required for accessibility (e.g., search inputs), use `outline_variant` (#c2c6d1) at **20% opacity**. It should be a whisper, not a shout.
*   **Glassmorphism:** Navigation rails should use semi-transparent `surface` with backdrop-blur, allowing the "scroll" of data to be faintly visible underneath, maintaining the user’s sense of place.

---

## 5. Components

### **Metrics Cards**
*   **Style:** No borders. Background: `surface-container-lowest`. 
*   **Layout:** High-contrast `headline-md` for the number, `label-md` for the descriptor.
*   **Interaction:** On hover, shift background to `surface-bright`.

### **Drag-and-Drop Zones**
*   **Style:** `surface-container-low` background. 
*   **Border:** A 2px dashed line using `primary` at 30% opacity. 
*   **Animation:** When a file is hovered, the background should transition to `primary_fixed` with a soft pulse.

### **Progress Bars (Extraction Status)**
*   **Track:** `surface-container-highest` (#e1e3e4).
*   **Indicator:** Gradient from `primary` to `surface_tint`. 
*   **Success State:** When complete, the indicator shifts to `tertiary_container` (#005613) with a `tertiary_fixed` glow.

### **Buttons**
*   **Primary:** `primary` (#003461) background with `on_primary` text. Use `xl` (0.75rem) roundedness for a modern, approachable feel.
*   **Secondary:** `surface-container-high` background. No border.
*   **Tertiary:** Text-only in `primary`, but with a `surface-container-lowest` background that appears only on hover.

### **Data Tables**
*   **Rule:** **No vertical or horizontal lines.** 
*   **Separation:** Use `8px` of vertical padding between rows. 
*   **Zebra Striping:** Use `surface-container-low` for even rows only when tables exceed 15 rows.

---

## 6. Do's and Don'ts

### **Do:**
*   **Do** use `2xl` spacing (32px+) between major content blocks to create an editorial feel.
*   **Do** use `tertiary` (Green) and `error` (Red) sparingly. They should act as "beacons" in a sea of blue and grey.
*   **Do** align all metrics to a strict baseline grid to ensure the tax data looks "audited" and precise.

### **Don't:**
*   **Don't** use 100% black text. Always use `on_surface` (#191c1d) to maintain a soft, premium contrast.
*   **Don't** use standard "Drop Shadows" from component libraries. Always use the Ambient Shadow formula defined in Section 4.
*   **Don't** use high-saturation icons. Icons should use `outline` (#727781) and only take on the `primary` color when active or hovered.
*   **Don't** use "Alert" banners that span the full width. Use floating "Toast" notifications with glassmorphism to avoid breaking the architectural grid.