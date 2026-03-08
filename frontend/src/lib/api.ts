/**
 * API client for the LLM Agent Backend.
 * Base URL from env (NEXT_PUBLIC_API_URL) or default localhost:8000.
 */

import type {
  Card,
  ChatResponse,
  DiscoveryResponse,
  MovieCard,
  MovieDetail,
  PersonCard,
  PersonDetail,
  TmdbConfig,
  TVCard,
  TvDetail,
} from "./types";

const getBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};

async function fetchApi<T>(
  path: string,
  options?: RequestInit & { params?: Record<string, string | number> }
): Promise<T> {
  const { params, ...init } = options ?? {};
  const url = new URL(path, getBaseUrl());
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }
  const res = await fetch(url.toString(), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    const message =
      res.status === 429
        ? "Rate limited — please wait a moment and try again."
        : (detail as { detail?: string }).detail || res.statusText;
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function getConfiguration(): Promise<TmdbConfig> {
  return fetchApi<TmdbConfig>("/configuration");
}

export async function postChat(message: string, region?: string | null): Promise<ChatResponse> {
  return fetchApi<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, region: region || undefined }),
  });
}

export async function getDiscoveryMoviesPopular(
  page = 1,
  language = "en-US",
  region?: string | null
): Promise<DiscoveryResponse<MovieCard>> {
  const params: Record<string, string | number> = { page, language };
  if (region && region.trim().length === 2) params.region = region.trim();
  return fetchApi<DiscoveryResponse<MovieCard>>("/discovery/movies/popular", {
    params,
  });
}

export async function getDiscoveryMoviesNowPlaying(
  page = 1,
  language = "en-US",
  region?: string | null
): Promise<DiscoveryResponse<MovieCard>> {
  const params: Record<string, string | number> = { page, language };
  if (region && region.trim().length === 2) params.region = region.trim();
  return fetchApi<DiscoveryResponse<MovieCard>>("/discovery/movies/now-playing", {
    params,
  });
}

export async function getDiscoveryTvPopular(
  page = 1,
  language = "en-US"
): Promise<DiscoveryResponse<TVCard>> {
  return fetchApi<DiscoveryResponse<TVCard>>("/discovery/tv/popular", {
    params: { page, language },
  });
}

export async function getDiscoveryPeopleTrending(
  time_window: "day" | "week" = "day",
  page = 1
): Promise<DiscoveryResponse<PersonCard>> {
  return fetchApi<DiscoveryResponse<PersonCard>>("/discovery/people/trending", {
    params: { time_window, page },
  });
}

export async function getMovieDetail(
  movieId: number,
  language = "en-US"
): Promise<MovieDetail> {
  return fetchApi<MovieDetail>(`/movies/${movieId}`, {
    params: { language },
  });
}

export async function getPersonDetail(
  personId: number,
  language = "en-US"
): Promise<PersonDetail> {
  return fetchApi<PersonDetail>(`/people/${personId}`, {
    params: { language },
  });
}

export async function getTvDetail(
  tvId: number,
  language = "en-US"
): Promise<TvDetail> {
  return fetchApi<TvDetail>(`/tv/${tvId}`, {
    params: { language },
  });
}

/**
 * Build poster or profile image URL from TMDb config and path.
 * Profile images use a larger size (h632 or w300) to avoid blur when displayed.
 */
export function buildImageUrl(
  config: TmdbConfig | null,
  path: string | null,
  size: "poster" | "profile" = "poster"
): string | null {
  if (!path || !config?.images?.secure_base_url) return null;
  const sizes = size === "profile"
    ? config.images.profile_sizes ?? config.images.poster_sizes ?? ["w185"]
    : config.images.poster_sizes ?? ["w342"];
  // Prefer larger sizes: profile → h632, w300, w185 to avoid blur; poster → w342, w500
  const preferred = size === "profile"
    ? ["h632", "w300", "w185"]
    : ["w500", "w342", "w780"];
  const s = preferred.find((p) => sizes.includes(p)) ?? sizes[sizes.length - 1] ?? sizes[0];
  return `${config.images.secure_base_url}${s}${path}`;
}
