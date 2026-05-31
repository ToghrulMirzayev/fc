import { ComingSoon } from "@/components/ComingSoon";
import { FeatureGate } from "@/components/FeatureGate";

export default function SchedulePage() {
  return (
    <FeatureGate feature="bookings">
      <ComingSoon
        crumbs={["Catalog", "Schedule"]}
        title="Schedule"
        headline="Your class calendar is being built."
        description="Plan recurring class slots, assign trainers, and set capacities. Members will be able to see and book classes straight from Telegram."
      />
    </FeatureGate>
  );
}
