"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useProfile, type Profile } from "./profile-context";

/**
 * Redirects to landing page if no profile exists.
 * Returns { profile, isReady } — only render page content when isReady && profile.
 */
export function useRequireProfile(): {
  profile: Profile | null;
  isReady: boolean;
} {
  const { profile, isLoaded } = useProfile();
  const router = useRouter();

  useEffect(() => {
    if (isLoaded && !profile) {
      router.replace("/");
    }
  }, [isLoaded, profile, router]);

  return { profile, isReady: isLoaded && profile !== null };
}
