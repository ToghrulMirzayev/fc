import type { QueryClient } from "@tanstack/react-query";

/**
 * Invalidate every cache entry a member-affecting action can change, so
 * the whole app reflects the new state immediately — no manual F5.
 *
 * Any mutation that can move a member's status or plan (assign, freeze,
 * resume, check-in, recording a payment) should call this on success.
 *
 * Covers:
 *  - ["members", ...] — the list page, all filter/search variants
 *    (react-query matches by key prefix, so ["members"] hits them all)
 *  - ["dashboard"]    — the home counters
 *  - ["checkins-feed"]— the live check-in feed
 *  - ["member", id] + ["member-visits", id] — that member's detail page
 */
export function invalidateMemberData(
  qc: QueryClient,
  memberId?: string,
): void {
  const keys: unknown[][] = [
    ["members"],
    ["dashboard"],
    ["checkins-feed"],
  ];
  if (memberId) {
    keys.push(["member", memberId], ["member-visits", memberId]);
  }
  for (const queryKey of keys) {
    // invalidate marks every matching query stale (so inactive ones
    // refetch when their page next mounts), and refetch forces any
    // currently-mounted query to update right now — without it, some
    // setups don't re-fetch the active query and the user needs F5.
    qc.invalidateQueries({ queryKey });
    qc.refetchQueries({ queryKey, type: "active" });
  }
}
