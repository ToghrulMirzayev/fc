import { ComingSoon } from "@/components/ComingSoon";

export default function SchedulePage() {
  return (
    <ComingSoon
      crumbs={["Catalog", "Schedule"]}
      title="Schedule"
      headline="Your class calendar is being built."
      description="Plan recurring class slots, assign trainers, and set capacities. Members will be able to see and book classes straight from Telegram."
    />
  );
}
