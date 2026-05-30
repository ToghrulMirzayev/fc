import { ComingSoon } from "@/components/ComingSoon";
import { FeatureGate } from "@/components/FeatureGate";

export default function BookingsPage() {
  return (
    <FeatureGate feature="bookings">
      <ComingSoon
        crumbs={["Operations", "Bookings"]}
        title="Bookings"
        headline="Class bookings are on the way."
        description="Soon you'll be able to schedule classes, manage trainer assignments, take reservations, and handle waitlists — all in one place."
      />
    </FeatureGate>
  );
}
