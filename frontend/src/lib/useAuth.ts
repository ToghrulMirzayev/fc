"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { fetchMe, tokens } from "@/lib/api";

/**
 * useAuth — fetches current user, handles auth redirects.
 *
 * Behavior:
 * - No token at all → redirect to /signup (new visitors land on marketing).
 * - Token present but request fails → redirect to /login (re-authenticate).
 *
 * Wrap protected pages with this. Returns user or null while loading.
 */
export function useAuth() {
  const router = useRouter();

  // Only run the query if we have a token. Without one we shouldn't
  // even ping the server — we just bounce to /signup.
  const hasToken = typeof window !== "undefined" && !!tokens.access;

  const query = useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
    retry: false,
    staleTime: 5 * 60_000,
    enabled: hasToken,
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!tokens.access) {
      router.replace("/signup");
      return;
    }
    if (query.isError) {
      // Token rejected by server. Wipe and send to login.
      tokens.clear();
      router.replace("/login");
    }
  }, [query.isError, router]);

  return { user: query.data, isLoading: query.isLoading };
}

/**
 * useFeature — true if a feature gate is enabled for the current tenant.
 *
 * Anything not explicitly enabled resolves to false, so callers should
 * HIDE the gated section/button entirely rather than disabling it.
 */
export function useFeature(key: string): boolean {
  const { user } = useAuth();
  return user?.features?.[key] === true;
}

export function useFeatures(): Record<string, boolean> {
  const { user } = useAuth();
  return user?.features ?? {};
}
