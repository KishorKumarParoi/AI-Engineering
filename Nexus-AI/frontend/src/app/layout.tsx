import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nexus-AI | Enterprise MLOps Platform",
  description:
    "Real-time ML model monitoring, Lakehouse analytics, and autonomous agent mesh dashboard",
  keywords: ["MLOps", "AI", "Lakehouse", "Dashboard", "Monitoring"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
