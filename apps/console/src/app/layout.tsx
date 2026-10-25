import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProofLayer — Enterprise Multilingual AI Agent Governance & Trust Gateway",
  description:
    "Runtime security, tool policy enforcement, cryptographic audit log, and automated red team engine for autonomous AI agents.",
  keywords: ["AI Security", "Prompt Injection", "Agent Governance", "Bangla AI", "Ed25519 Audit Log"],
  authors: [{ name: "ProofLayer Team" }],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090d16] text-gray-100 antialiased selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
