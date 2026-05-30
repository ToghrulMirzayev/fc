"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/useAuth";

/**
 * FeatureGate — wraps a page whose access is controlled by a feature flag.
 *
 * If the feature isn't enabled for the current tenant, the page content is
 * never rendered and the user is bounced to the dashboard. This is the
 * route-level mirror of the Sidebar hiding the nav link, so a gated
 * section can't be reached by typing the URL.
 */
export function FeatureGate({
  feature,
  children,
}: {
  feature: string;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const enabled = user?.features?.[feature] === true;

  useEffect(() => {
    if (!isLoading && user && !enabled) {
      router.replace("/");
    }
  }, [isLoading, user, enabled, router]);

  if (!user || !enabled) return null;
  return <>{children}</>;
}
