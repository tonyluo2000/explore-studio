import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://course4teen.com"),
  title: "Course4Teen | Learn Python by Building a World",
  description:
    "A live, small-group coding course where teens learn real Python by building an interactive world across 30 guided sessions.",
  keywords: [
    "coding course for teens",
    "Python for teens",
    "live online coding class",
    "Explore Studio",
  ],
  alternates: { canonical: "/" },
  openGraph: {
    title: "Course4Teen | Learn Python by Building a World",
    description:
      "Thirty live, 45-minute sessions. One world teens can make their own.",
    url: "/",
    siteName: "Course4Teen",
    type: "website",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#101e2d",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
