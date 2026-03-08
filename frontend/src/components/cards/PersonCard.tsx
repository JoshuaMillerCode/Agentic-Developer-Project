"use client";

import Link from "next/link";
import type { TmdbConfig } from "@/lib/types";
import { buildImageUrl } from "@/lib/api";
import type { PersonCard as PersonCardType } from "@/lib/types";

export function PersonCard({
  card,
  config,
  size = "normal",
}: {
  card: PersonCardType;
  config: TmdbConfig | null;
  size?: "normal" | "compact";
}) {
  const profileUrl = buildImageUrl(config, card.profile_path, "profile");

  if (size === "compact") {
    return (
      <Link href={`/person/${card.id}`} className="group flex-shrink-0 w-24 sm:w-28 rounded-lg overflow-hidden bg-surface-700 transition transform hover:scale-105 hover:ring-2 hover:ring-accent-red/60 block">
        <div className="aspect-[2/3] relative bg-surface-600 overflow-hidden">
          {profileUrl ? (
            <img
              src={profileUrl}
              alt={card.name ?? "Person"}
              className="w-full h-full object-cover object-top"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-500 text-xs">
              No photo
            </div>
          )}
        </div>
        <div className="p-1.5">
          <p className="font-medium text-xs text-white truncate" title={card.name ?? undefined}>
            {card.name ?? "Unknown"}
          </p>
          {card.known_for_department && (
            <p className="text-[10px] text-gray-400 truncate">{card.known_for_department}</p>
          )}
        </div>
      </Link>
    );
  }

  return (
    <Link href={`/person/${card.id}`} className="group flex-shrink-0 w-36 sm:w-44 rounded-xl overflow-hidden bg-surface-700 transition transform hover:scale-[1.02] hover:shadow-xl hover:shadow-black/30 hover:ring-2 hover:ring-accent-red/50 block">
      <article>
      <div className="aspect-[2/3] relative bg-surface-600 overflow-hidden">
        {profileUrl ? (
          <img
            src={profileUrl}
            alt={card.name ?? "Person"}
            className="w-full h-full object-cover object-top"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500 text-sm">
            No photo
          </div>
        )}
      </div>
      <div className="p-3">
        <h3 className="font-semibold text-white truncate" title={card.name ?? undefined}>
          {card.name ?? "Unknown"}
        </h3>
        {card.known_for_department && (
          <p className="text-sm text-accent-gold/90">{card.known_for_department}</p>
        )}
        {card.known_for && card.known_for.length > 0 && (
          <p className="mt-1 text-xs text-gray-400 truncate" title={card.known_for.join(", ")}>
            {card.known_for.slice(0, 3).join(", ")}
          </p>
        )}
        {card.biography && (
          <p className="mt-2 text-xs text-gray-500 line-clamp-3">{card.biography}</p>
        )}
      </div>
      </article>
    </Link>
  );
}
