"use client";

import { useState, useCallback, useEffect } from "react";
import { postChat } from "@/lib/api";
import type { Card, ChatResponse, TmdbConfig } from "@/lib/types";
import { CardRenderer } from "@/components/cards";
import { ChatLoading } from "./ChatLoading";

const PLACEHOLDER =
  "Ask me anything — first date movies, 90s thrillers, shows like Breaking Bad...";

const CHAT_STORAGE_KEY = "aiMovieAssistantChat";

function loadStoredResponse(): ChatResponse | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(CHAT_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as ChatResponse;
    if (parsed && typeof parsed.response === "string" && Array.isArray(parsed.cards)) return parsed;
    return null;
  } catch {
    return null;
  }
}

function saveResponse(data: ChatResponse) {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(data));
  } catch {
    // ignore
  }
}

export function ChatSection({
  config,
  region,
}: {
  config: TmdbConfig | null;
  region?: string | null;
}) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);

  useEffect(() => {
    const stored = loadStoredResponse();
    if (stored) setLastResponse(stored);
  }, []);

  const sendMessage = useCallback(async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setLoading(true);
    setError(null);
    setLastResponse(null);
    try {
      const res = await postChat(msg, region || undefined);
      setLastResponse(res);
      saveResponse(res);
      setInput("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }, [input, loading, region]);

  return (
    <section className="w-full max-w-4xl mx-auto px-4 pt-6 pb-8">
      {/* Hero input — always on top */}
      <div className="relative">
        <div className="flex gap-2 rounded-2xl bg-surface-800 border border-surface-600 shadow-xl focus-within:ring-2 focus-within:ring-accent-red/50 focus-within:border-accent-red/30 transition-all">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder={PLACEHOLDER}
            disabled={loading}
            className="flex-1 min-w-0 bg-transparent px-5 py-4 text-gray-100 placeholder-gray-500 outline-none text-base sm:text-lg"
            aria-label="Ask the AI assistant"
          />
          <button
            type="button"
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="flex-shrink-0 px-5 py-4 font-semibold text-white bg-accent-red hover:bg-accent-redDim disabled:opacity-50 disabled:cursor-not-allowed rounded-r-2xl transition-colors"
          >
            {loading ? "..." : "Ask"}
          </button>
        </div>
        {error && (
          <p className="mt-2 text-sm text-red-400 animate-fade-in" role="alert">
            {error}
          </p>
        )}
      </div>

      {/* Loading: film strip + "Searching the vault..." */}
      {loading && <ChatLoading />}

      {/* Response + cards — smooth transition below input */}
      {lastResponse && (
        <div className="mt-8 animate-slide-up space-y-6">
          <div className="prose prose-invert max-w-none">
            <p className="text-gray-200 leading-relaxed whitespace-pre-wrap">
              {lastResponse.response}
            </p>
          </div>
          {lastResponse.cards && lastResponse.cards.length > 0 && (
            <div className="flex flex-wrap gap-4 justify-start">
              {(lastResponse.cards as Card[]).map((card) => (
                <CardRenderer
                  key={`${card.type}-${card.id}`}
                  card={card}
                  config={config}
                  size="normal"
                />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
