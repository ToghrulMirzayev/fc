import { ComingSoon } from "@/components/ComingSoon";

export default function BookingsPage() {
  return (
    <ComingSoon
      crumbs={["Operations", "Bookings"]}
      title="Bookings"
      headline="Class bookings are on the way."
      description="Soon you'll be able to schedule classes, manage trainer assignments, take reservations, and handle waitlists — all in one place."
    />
  );
}
