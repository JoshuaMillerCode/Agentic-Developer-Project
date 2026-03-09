"use client";

import { useEffect, useState } from "react";
import { getConfiguration } from "@/lib/api";
import type { TmdbConfig } from "@/lib/types";
import { ChatSection } from "@/components/chat";
import { DiscoverySection } from "@/components/discovery";

export default function Home() {
  const [config, setConfig] = useState<TmdbConfig | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);

  useEffect(() => {
    getConfiguration()
      .then(setConfig)
      .catch((e) => setConfigError(e instanceof Error ? e.message : "Failed to load config."));
  }, []);

  return (
    <main className="min-h-screen bg-surface-900">
      {/* Hero: AI assistant always on top */}
      <header className="pt-8 pb-2">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Reel Recs
          </h1>
          <p className="mt-2 text-gray-400 text-sm sm:text-base">
            AI-powered movie & TV picks — ask in plain English.
          </p>
        </div>
      </header>

      {configError && (
        <div className="max-w-4xl mx-auto px-4 py-2 text-center text-amber-500 text-sm" role="alert">
          {configError} Poster images may not load.
        </div>
      )}

      <ChatSection config={config} />

      {/* Discovery sections below */}
      <DiscoverySection config={config} />
    </main>
  );
}
