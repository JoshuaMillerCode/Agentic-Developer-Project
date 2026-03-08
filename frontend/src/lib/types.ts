/**
 * Types matching backend card shapes and API responses.
 * All data is fetched via the backend; no API keys on the client.
 */

export type MovieCard = {
  type: "movie";
  id: number;
  title: string | null;
  poster_path: string | null;
  release_date: string | null;
  vote_average: number | null;
  overview: string | null;
};

export type TVCard = {
  type: "tv";
  id: number;
  name: string | null;
  poster_path: string | null;
  first_air_date: string | null;
  vote_average: number | null;
  overview: string | null;
};

export type PersonCard = {
  type: "person";
  id: number;
  name: string | null;
  profile_path: string | null;
  known_for_department: string | null;
  known_for: string[];
  biography: string | null;
};

export type Card = MovieCard | TVCard | PersonCard;

export type TmdbConfig = {
  images?: {
    base_url?: string;
    secure_base_url?: string;
    poster_sizes?: string[];
    profile_sizes?: string[];
  };
};

export type ChatResponse = {
  response: string;
  reply_found: boolean;
  cards: Card[];
};

export type DiscoveryResponse<T> = {
  results: T[];
  page: number;
  total_pages: number;
  total_results: number;
};

export type CastMember = {
  id: number;
  name: string | null;
  character: string | null;
  profile_path: string | null;
};

export type MovieDetail = {
  type: "movie";
  id: number;
  title: string | null;
  poster_path: string | null;
  release_date: string | null;
  vote_average: number | null;
  overview: string | null;
  tagline: string | null;
  genres: { id: number; name: string }[];
  runtime: number | null;
  cast: CastMember[];
};

export type PersonDetail = {
  type: "person";
  id: number;
  name: string | null;
  profile_path: string | null;
  known_for_department: string | null;
  known_for: string[];
  biography: string | null;
  birthday: string | null;
  place_of_birth: string | null;
  movie_credits: { id?: number; title?: string; release_date?: string; character?: string }[];
  tv_credits: { id?: number; name?: string; first_air_date?: string; character?: string }[];
};

export type TvDetail = {
  type: "tv";
  id: number;
  name: string | null;
  poster_path: string | null;
  first_air_date: string | null;
  vote_average: number | null;
  overview: string | null;
  tagline: string | null;
  genres: { id: number; name: string }[];
  number_of_seasons: number | null;
  cast: CastMember[];
};
