import { appName } from "@/lib/branding";

/**
 * Barbell brand mark — a stylized barbell with orange accent plates.
 *
 * Composition (left-to-right):
 *   outer plate (black, tall) — main weight
 *   accent plate (orange, slightly shorter) — brand color
 *   inner plate (black, shorter) — secondary weight
 *   shaft (horizontal black bar) connecting both sides, mirrored
 *
 * Drawn into a 100×32 viewBox so it sits naturally inline with text.
 * Strokes use real shapes (rects), not stroke-width, so scaling stays crisp.
 */
export function LogoMark({
  size = 32,
  className,
}: {
  size?: number;
  className?: string;
}) {
  // Maintain proportions of the source logo: barbell ~3.5× wider than tall.
  const w = size * 3.125;
  const h = size;
  return (
    <svg
      width={w}
      height={h}
      viewBox="0 0 100 32"
      className={className}
      role="img"
      aria-label="Fitness Court barbell mark"
    >
      {/* Shaft */}
      <rect x="22" y="14.5" width="56" height="3" fill="currentColor" />

      {/* Left side — outer plate, accent plate, inner plate */}
      <rect x="6" y="4" width="6" height="24" rx="0.5" fill="currentColor" />
      <rect x="13" y="6" width="4" height="20" rx="0.5" fill="var(--color-accent)" />
      <rect x="18" y="9" width="4" height="14" rx="0.5" fill="currentColor" />

      {/* Right side — mirror */}
      <rect x="78" y="9" width="4" height="14" rx="0.5" fill="currentColor" />
      <rect x="83" y="6" width="4" height="20" rx="0.5" fill="var(--color-accent)" />
      <rect x="88" y="4" width="6" height="24" rx="0.5" fill="currentColor" />
    </svg>
  );
}

/**
 * Mark + wordmark, side by side. The wordmark uses the app name from the
 * branding module so changing APP_NAME rebrands the whole app.
 */
export function Logo({
  size = 28,
  showWordmark = true,
}: {
  size?: number;
  showWordmark?: boolean;
}) {
  return (
    <div className="flex items-center gap-3 text-primary">
      <LogoMark size={size} />
      {showWordmark && (
        <span className="font-bold uppercase tracking-tight text-primary"
              style={{ fontSize: size * 0.62, lineHeight: 1 }}>
          {appName()}
        </span>
      )}
    </div>
  );
}
