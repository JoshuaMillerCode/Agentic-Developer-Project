"use client";

import Link from "next/link";
import type { TmdbConfig } from "@/lib/types";
import { buildImageUrl } from "@/lib/api";
import type { MovieCard as MovieCardType } from "@/lib/types";

function voteColor(vote: number | null): string {
  if (vote == null) return "bg-gray-600";
  if (vote >= 7.5) return "bg-emerald-500";
  if (vote >= 6) return "bg-amber-500";
  if (vote >= 4) return "bg-orange-500";
  return "bg-red-500";
}

export function MovieCard({
  card,
  config,
  size = "normal",
}: {
  card: MovieCardType;
  config: TmdbConfig | null;
  size?: "normal" | "compact";
}) {
  const posterUrl = buildImageUrl(config, card.poster_path, "poster");
  const year = card.release_date ? new Date(card.release_date).getFullYear() : null;

  if (size === "compact") {
    return (
      <Link href={`/movie/${card.id}`} className="group flex-shrink-0 w-28 sm:w-36 rounded-lg overflow-hidden bg-surface-700 transition transform hover:scale-105 hover:ring-2 hover:ring-accent-red/60 block">
        <div className="block aspect-[2/3] relative bg-surface-600">
          {posterUrl ? (
            <img
              src={posterUrl}
              alt={card.title ?? "Movie"}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-500 text-xs">
              No image
            </div>
          )}
          {card.vote_average != null && (
            <span
              className={`absolute top-1 right-1 px-1.5 py-0.5 rounded text-xs font-bold text-white ${voteColor(card.vote_average)}`}
            >
              {card.vote_average.toFixed(1)}
            </span>
          )}
        </div>
        <div className="p-1.5">
          <p className="font-medium text-sm text-white truncate" title={card.title ?? undefined}>
            {card.title ?? "Untitled"}
          </p>
          {year != null && <p className="text-xs text-gray-400">{year}</p>}
        </div>
      </Link>
    );
  }

  return (
    <Link href={`/movie/${card.id}`} className="group flex-shrink-0 w-40 sm:w-48 rounded-xl overflow-hidden bg-surface-700 transition transform hover:scale-[1.02] hover:shadow-xl hover:shadow-black/30 hover:ring-2 hover:ring-accent-red/50 block">
      <article>
      <div className="relative aspect-[2/3] bg-surface-600">
        {posterUrl ? (
          <img
            src={posterUrl}
            alt={card.title ?? "Movie"}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500 text-sm">
            No image
          </div>
        )}
        {card.vote_average != null && (
          <span
            className={`absolute top-2 right-2 px-2 py-1 rounded-md text-sm font-bold text-white shadow ${voteColor(card.vote_average)}`}
          >
            {card.vote_average.toFixed(1)}
          </span>
        )}
      </div>
      <div className="p-3">
        <h3 className="font-semibold text-white truncate" title={card.title ?? undefined}>
          {card.title ?? "Untitled"}
        </h3>
        <p className="text-sm text-gray-400">
          {year != null ? year : "—"}
        </p>
        {card.overview && (
          <p className="mt-2 text-xs text-gray-500 line-clamp-3">{card.overview}</p>
        )}
      </div>
      </article>
    </Link>
  );
}
