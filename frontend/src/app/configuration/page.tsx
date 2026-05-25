import { ComingSoon } from "@/components/ComingSoon";

export default function ConfigurationPage() {
  return (
    <ComingSoon
      crumbs={["Settings", "Configuration"]}
      title="Configuration"
      headline="Workspace settings will live here."
      description="Edit your gym profile, branding, branches, anti-passback cooldown, currency, QR code lifetime, and more."
    />
  );
}
