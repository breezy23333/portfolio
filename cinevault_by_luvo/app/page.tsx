// app/page.tsx
export const dynamic = "force-dynamic";

import {
  getPopularMovies,
  getTrendingAll,
  getMovieGenres,
} from "@/lib/fetchers";

import HeroCarousel from "@/components/HeroCarousel";
import CategoriesTray from "@/components/CategoriesTray";
import dynamicImport from "next/dynamic";
import type { ReactNode } from "react";

/* ---------------- helpers ---------------- */

const withTimeout = <T,>(p: Promise<T>, ms = 8000) =>
  Promise.race<T>([
    p,
    new Promise<T>((_, rej) =>
      setTimeout(() => rej(new Error("timeout")), ms)
    ) as T,
  ]);

/* ---------------- dynamic components ---------------- */

const ShelfRow = dynamicImport(() => import("@/components/ShelfRow"), {
  ssr: true,
  loading: () => <RowSkeleton />,
});

/* ---------------- page ---------------- */

export default async function Home() {
  let popularRaw: any[] = [];
  let trendingRaw: any[] = [];
  let genres: any[] = [];

  try {
    const [popularRes, trendingRes, genreRes] =
      await Promise.allSettled([
        withTimeout(getPopularMovies(1)),
        withTimeout(getTrendingAll(1)),
        withTimeout(getMovieGenres()),
      ]);

    if (popularRes.status === "fulfilled")
      popularRaw = popularRes.value?.results ?? [];

    if (trendingRes.status === "fulfilled")
      trendingRaw = trendingRes.value?.results ?? [];

    if (genreRes.status === "fulfilled" && Array.isArray(genreRes.value))
      genres = genreRes.value;
  } catch (e) {
    console.error("Home fetch failed", e);
  }

const heroItems = trendingRaw.slice(0, 10).map((m) => ({
  id: m.id,
  media: m.media_type ?? "movie",
  title: m.title || m.name,
  overview: m.overview,
  poster: m.poster_path
    ? `https://image.tmdb.org/t/p/w780${m.poster_path}`
    : null,
  backdrop: m.backdrop_path
    ? `https://image.tmdb.org/t/p/w1280${m.backdrop_path}`
    : null,
  year: (m.release_date || m.first_air_date || "").slice(0, 4),
  rating: m.vote_average,
}));


return (
  <main className="pb-10">
    {/* 🔥 HERO SECTION */}
    <HeroCarousel items={heroItems} />

    {/* 🔽 CONTENT SURFACE */}
    <Surface>
      <div className="space-y-6">
        {genres.length > 0 && <CategoriesTray genres={genres} />}

        <Panel title="More movies">
          <ShelfRow items={popularRaw} />
        </Panel>

        <Panel title="Trending movies">
          <ShelfRow items={trendingRaw} />
        </Panel>
      </div>
    </Surface>
  </main>
);

}

/* ---------------- UI helpers ---------------- */

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl bg-[#0c111b] ring-1 ring-white/10 overflow-hidden">
      <div className="px-4 md:px-6 py-3 md:py-4">
        <h2 className="text-lg md:text-xl font-bold">{title}</h2>
      </div>
      <div className="px-2 md:px-4 pb-4">{children}</div>
    </section>
  );
}

function Surface({ children }: { children: ReactNode }) {
  return (
    <section className="relative z-10 w-[100svw] left-1/2 -translate-x-1/2 -mt-8 md:-mt-10">
      <div className="relative bg-[#0e131f] rounded-t-[28px] ring-1 ring-white/10">
        <div className="mx-auto max-w-[1600px] px-4 md:px-8 pt-6 pb-8 space-y-6">
          {children}
        </div>
      </div>
    </section>
  );
}

function RowSkeleton() {
  return (
    <div className="flex gap-4 overflow-hidden">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="h-[270px] w-[180px] rounded-xl bg-white/5 animate-pulse"
        />
      ))}
    </div>
  );
}


