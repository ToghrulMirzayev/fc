import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { copy } from "@/lib/branding";
import { Providers } from "@/components/Providers";
import { CookieConsent } from "@/components/CookieConsent";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: copy.appFullTitle(),
  description: "Modern multi-tenant SaaS for gyms and fitness studios.",
  icons: {
    icon: [{ url: "/favicon.ico?v=5", sizes: "any" }],
    shortcut: "/favicon.ico?v=5",
  },
};

/**
 * The `data-theme` attribute defaults to "dark" on the server so the
 * initial paint matches what ThemeProvider will set after hydration.
 * If the user prefers light, there'll be a brief dark flash — acceptable
 * for v1.0; can be eliminated with a tiny inline script later.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="dark" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-ink text-primary antialiased">
        <Providers>{children}</Providers>
        <CookieConsent />
      </body>
    </html>
  );
}
