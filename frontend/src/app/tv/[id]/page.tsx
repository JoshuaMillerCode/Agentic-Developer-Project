"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getConfiguration, getTvDetail, buildImageUrl } from "@/lib/api";
import type { TmdbConfig } from "@/lib/types";

function voteColor(vote: number | null): string {
  if (vote == null) return "bg-gray-600";
  if (vote >= 7.5) return "bg-emerald-500";
  if (vote >= 6) return "bg-amber-500";
  if (vote >= 4) return "bg-orange-500";
  return "bg-red-500";
}

export default function TvPage() {
  const params = useParams();
  const id = typeof params?.id === "string" ? parseInt(params.id, 10) : NaN;
  const [config, setConfig] = useState<TmdbConfig | null>(null);
  const [show, setShow] = useState<Awaited<ReturnType<typeof getTvDetail>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(id) || id < 1) {
      setError("Invalid TV show ID");
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([getConfiguration(), getTvDetail(id)])
      .then(([cfg, detail]) => {
        if (!cancelled) {
          setConfig(cfg);
          setShow(detail);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load show.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-900 flex items-center justify-center">
        <p className="text-gray-400">Loading…</p>
      </div>
    );
  }

  if (error || !show) {
    return (
      <div className="min-h-screen bg-surface-900 px-4 py-12">
        <div className="max-w-2xl mx-auto text-center">
          <p className="text-red-400 mb-4">{error ?? "Show not found."}</p>
          <Link href="/" className="text-accent-red hover:underline">
            ← Back to home
          </Link>
        </div>
      </div>
    );
  }

  const posterUrl = buildImageUrl(config, show.poster_path, "poster");
  const year = show.first_air_date ? new Date(show.first_air_date).getFullYear() : null;
  const genreNames = show.genres?.map((g) => g.name).filter(Boolean).join(", ") || null;

  return (
    <div className="min-h-screen bg-surface-900">
      <header className="border-b border-surface-700">
        <div className="max-w-5xl mx-auto px-4 py-3">
          <Link href="/" className="text-gray-400 hover:text-white text-sm">
            ← Back to Reel Recs
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex flex-col sm:flex-row gap-8">
          <div className="flex-shrink-0 w-full sm:w-72">
            <div className="aspect-[2/3] rounded-xl overflow-hidden bg-surface-700">
              {posterUrl ? (
                <img
                  src={posterUrl}
                  alt={show.name ?? "TV poster"}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-500">
                  No image
                </div>
              )}
            </div>
            {show.vote_average != null && (
              <div className="mt-3 flex items-center gap-2">
                <span
                  className={`inline-flex px-2 py-1 rounded text-sm font-bold text-white ${voteColor(show.vote_average)}`}
                >
                  {show.vote_average.toFixed(1)}
                </span>
                <span className="text-gray-400 text-sm">Rating</span>
              </div>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <h1 className="text-3xl font-bold text-white">
              {show.name ?? "Untitled"}
            </h1>
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-gray-400 text-sm">
              {year != null && <span>{year}</span>}
              {show.number_of_seasons != null && show.number_of_seasons > 0 && (
                <span>{show.number_of_seasons} season{show.number_of_seasons !== 1 ? "s" : ""}</span>
              )}
              {genreNames && <span>{genreNames}</span>}
            </div>
            {show.tagline && (
              <p className="mt-3 text-lg text-gray-300 italic">&ldquo;{show.tagline}&rdquo;</p>
            )}
            {show.overview && (
              <div className="mt-4">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
                  Overview
                </h2>
                <p className="mt-2 text-gray-200 leading-relaxed">{show.overview}</p>
              </div>
            )}

            {show.cast && show.cast.length > 0 && (
              <div className="mt-8">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
                  Cast
                </h2>
                <ul className="flex flex-wrap gap-4">
                  {show.cast.slice(0, 12).map((member) => {
                    const profileUrl = buildImageUrl(config, member.profile_path, "profile");
                    return (
                      <li key={member.id} className="flex-shrink-0 w-24 text-center">
                        <Link href={`/person/${member.id}`} className="block group">
                          <div className="aspect-[2/3] rounded-lg overflow-hidden bg-surface-700 group-hover:ring-2 group-hover:ring-accent-red/50 transition">
                            {profileUrl ? (
                              <img
                                src={profileUrl}
                                alt={member.name ?? ""}
                                className="w-full h-full object-cover object-top"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-gray-500 text-xs">
                                No photo
                              </div>
                            )}
                          </div>
                          <p className="mt-1 text-sm font-medium text-white truncate group-hover:text-accent-red transition" title={member.name ?? undefined}>
                            {member.name ?? "—"}
                          </p>
                          {member.character && (
                            <p className="text-xs text-gray-500 truncate" title={member.character}>
                              {member.character}
                            </p>
                          )}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
