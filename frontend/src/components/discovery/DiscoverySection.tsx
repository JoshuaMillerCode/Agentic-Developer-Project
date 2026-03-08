"use client";

import { useEffect, useState } from "react";
import {
  getDiscoveryMoviesPopular,
  getDiscoveryMoviesNowPlaying,
  getDiscoveryTvPopular,
  getDiscoveryPeopleTrending,
} from "@/lib/api";
import type {
  MovieCard as MovieCardType,
  TVCard as TVCardType,
  PersonCard as PersonCardType,
  TmdbConfig,
} from "@/lib/types";
import { CardRenderer } from "@/components/cards";
import type { Card } from "@/lib/types";

type RowItem = Card;

export function DiscoverySection({
  config,
  region,
}: {
  config: TmdbConfig | null;
  region?: string | null;
}) {
  const [popularMovies, setPopularMovies] = useState<MovieCardType[]>([]);
  const [nowPlaying, setNowPlaying] = useState<MovieCardType[]>([]);
  const [popularTv, setPopularTv] = useState<TVCardType[]>([]);
  const [trendingPeople, setTrendingPeople] = useState<PersonCardType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      getDiscoveryMoviesPopular(1, "en-US", region).then((r) => r.results),
      getDiscoveryMoviesNowPlaying(1, "en-US", region).then((r) => r.results),
      getDiscoveryTvPopular(1).then((r) => r.results),
      getDiscoveryPeopleTrending("day", 1).then((r) => r.results),
    ])
      .then(([movies, playing, tv, people]) => {
        if (!cancelled) {
          setPopularMovies(movies);
          setNowPlaying(playing);
          setPopularTv(tv);
          setTrendingPeople(people);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load discovery.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [region]);

  if (loading) {
    return (
      <section className="w-full px-4 py-12">
        <div className="max-w-6xl mx-auto text-center text-gray-400">
          Loading discovery…
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="w-full px-4 py-12">
        <div className="max-w-6xl mx-auto text-center text-red-400" role="alert">
          {error}
        </div>
      </section>
    );
  }

  function Row({
    title,
    items,
  }: {
    title: string;
    items: RowItem[];
  }) {
    return (
      <div className="mb-10 overflow-visible">
        <h2 className="text-xl font-bold text-white mb-4 px-1">{title}</h2>
        <div className="flex gap-4 overflow-x-auto overflow-y-visible scroll-row py-4 pb-2 px-2">
          {items.map((card) => (
            <CardRenderer
              key={`${card.type}-${card.id}`}
              card={card}
              config={config}
              size="compact"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <section className="w-full px-4 py-8 border-t border-surface-700">
      <div className="max-w-6xl mx-auto">
        <Row title="Currently Popular Movies" items={popularMovies} />
        <Row title="Now Playing in Theaters" items={nowPlaying} />
        <Row title="Popular TV Series" items={popularTv} />
        <Row title="Trending Actors" items={trendingPeople} />
      </div>
    </section>
  );
}
