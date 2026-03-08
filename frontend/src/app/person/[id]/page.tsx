"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getConfiguration, getPersonDetail, buildImageUrl } from "@/lib/api";
import type { TmdbConfig } from "@/lib/types";

export default function PersonPage() {
  const params = useParams();
  const id = typeof params?.id === "string" ? parseInt(params.id, 10) : NaN;
  const [config, setConfig] = useState<TmdbConfig | null>(null);
  const [person, setPerson] = useState<Awaited<ReturnType<typeof getPersonDetail>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(id) || id < 1) {
      setError("Invalid person ID");
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([getConfiguration(), getPersonDetail(id)])
      .then(([cfg, detail]) => {
        if (!cancelled) {
          setConfig(cfg);
          setPerson(detail);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load person.");
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

  if (error || !person) {
    return (
      <div className="min-h-screen bg-surface-900 px-4 py-12">
        <div className="max-w-2xl mx-auto text-center">
          <p className="text-red-400 mb-4">{error ?? "Person not found."}</p>
          <Link href="/" className="text-accent-red hover:underline">
            ← Back to home
          </Link>
        </div>
      </div>
    );
  }

  const profileUrl = buildImageUrl(config, person.profile_path, "profile");

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
          <div className="flex-shrink-0 w-full sm:w-64">
            <div className="aspect-[2/3] max-w-xs rounded-xl overflow-hidden bg-surface-700">
              {profileUrl ? (
                <img
                  src={profileUrl}
                  alt={person.name ?? "Profile"}
                  className="w-full h-full object-cover object-top"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-500">
                  No photo
                </div>
              )}
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <h1 className="text-3xl font-bold text-white">
              {person.name ?? "Unknown"}
            </h1>
            {person.known_for_department && (
              <p className="mt-2 text-accent-gold/90">{person.known_for_department}</p>
            )}
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-gray-400 text-sm">
              {person.birthday && <span>Born {person.birthday}</span>}
              {person.place_of_birth && <span>{person.place_of_birth}</span>}
            </div>

            {person.biography && (
              <div className="mt-6">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
                  Biography
                </h2>
                <p className="mt-2 text-gray-200 leading-relaxed whitespace-pre-line">
                  {person.biography}
                </p>
              </div>
            )}

            {person.known_for && person.known_for.length > 0 && (
              <div className="mt-6">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
                  Known for
                </h2>
                <p className="text-gray-300">{person.known_for.join(", ")}</p>
              </div>
            )}

            {person.movie_credits && person.movie_credits.length > 0 && (
              <div className="mt-8">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
                  Movie credits
                </h2>
                <ul className="space-y-2">
                  {person.movie_credits.slice(0, 10).map((c, i) => (
                    <li key={c.id ?? i} className="text-gray-200">
                      {c.id ? (
                        <Link href={`/movie/${c.id}`} className="font-medium text-white hover:text-accent-red transition">
                          {c.title ?? "—"}
                        </Link>
                      ) : (
                        <span className="font-medium">{c.title ?? "—"}</span>
                      )}
                      {c.character && (
                        <span className="text-gray-500"> as {c.character}</span>
                      )}
                      {c.release_date && (
                        <span className="text-gray-400 text-sm ml-2">({c.release_date?.slice(0, 4)})</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {person.tv_credits && person.tv_credits.length > 0 && (
              <div className="mt-6">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
                  TV credits
                </h2>
                <ul className="space-y-2">
                  {person.tv_credits.slice(0, 10).map((c, i) => (
                    <li key={c.id ?? i} className="text-gray-200">
                      {c.id ? (
                        <Link href={`/tv/${c.id}`} className="font-medium text-white hover:text-accent-red transition">
                          {c.name ?? "—"}
                        </Link>
                      ) : (
                        <span className="font-medium">{c.name ?? "—"}</span>
                      )}
                      {c.character && (
                        <span className="text-gray-500"> as {c.character}</span>
                      )}
                      {c.first_air_date && (
                        <span className="text-gray-400 text-sm ml-2">({c.first_air_date?.slice(0, 4)})</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
