"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export function CookieConsent() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if the user has already consented
    const consent = localStorage.getItem("cookie-consent-accepted");
    if (!consent) {
      // Small delay for smooth entry animation
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem("cookie-consent-accepted", "true");
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-6 left-6 right-6 md:left-auto md:right-6 z-50 max-w-md animate-fade-in-up">
      <div className="rounded-lg border border-subtle bg-card/90 p-5 shadow-2xl backdrop-blur-md flex flex-col gap-4">
        <div>
          <h4 className="text-md font-semibold text-primary mb-1">
            Cookie Consent
          </h4>
          <p className="text-sm text-secondary leading-relaxed">
            We use cookies (specifically secure authentication tokens) to provide, 
            protect, and improve our services. By clicking "OK" or continuing to 
            use our platform, you agree to our use of cookies as described in our{" "}
            <Link href="/privacy" className="text-coral underline hover:text-coral-dim">
              Privacy Policy
            </Link>.
          </p>
        </div>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={handleAccept}
            className="rounded-md bg-coral px-5 py-2 text-sm font-medium text-white hover:bg-coral-dim transition-colors cursor-pointer"
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
}
