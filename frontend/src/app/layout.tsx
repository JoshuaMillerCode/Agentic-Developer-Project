import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Reel Recs — Movie & TV Picks",
  description:
    "Discover movies, TV shows, and actors. Ask in plain English — first date movies, 90s thrillers, shows like Breaking Bad.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-surface-900 text-gray-100 antialiased">
        {children}
      </body>
    </html>
  );
}
