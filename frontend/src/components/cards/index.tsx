"use client";

import type { Card, TmdbConfig } from "@/lib/types";
import { MovieCard } from "./MovieCard";
import { TVCard } from "./TVCard";
import { PersonCard } from "./PersonCard";

export function CardRenderer({
  card,
  config,
  size = "normal",
}: {
  card: Card;
  config: TmdbConfig | null;
  size?: "normal" | "compact";
}) {
  if (card.type === "movie") return <MovieCard card={card} config={config} size={size} />;
  if (card.type === "tv") return <TVCard card={card} config={config} size={size} />;
  if (card.type === "person") return <PersonCard card={card} config={config} size={size} />;
  return null;
}

export { MovieCard, TVCard, PersonCard };
