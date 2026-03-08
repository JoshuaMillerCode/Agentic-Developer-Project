"use client";

/**
 * Movie-themed loading indicator: scrolling film strip + fun copy.
 * Shown while the AI is thinking after the user sends a message.
 */
export function ChatLoading() {
  return (
    <div
      className="mt-8 flex flex-col items-center gap-6 animate-fade-in"
      role="status"
      aria-live="polite"
      aria-label="AI is thinking"
    >
      {/* Film strip: row of "frames" that scroll */}
      <div className="relative w-full max-w-md overflow-hidden rounded-lg bg-surface-800/80 border border-surface-600 py-4">
        <div className="film-strip-track flex gap-2">
          {[...Array(12)].map((_, i) => (
            <div
              key={i}
              className="flex-shrink-0 w-12 h-16 rounded bg-surface-700 border border-surface-600 film-frame"
              aria-hidden
            />
          ))}
          {/* Duplicate for seamless loop */}
          {[...Array(12)].map((_, i) => (
            <div
              key={`dup-${i}`}
              className="flex-shrink-0 w-12 h-16 rounded bg-surface-700 border border-surface-600 film-frame"
              aria-hidden
            />
          ))}
        </div>
      </div>

      <p className="text-gray-400 text-sm font-medium animate-pulse">
        Searching the vault…
      </p>
    </div>
  );
}
