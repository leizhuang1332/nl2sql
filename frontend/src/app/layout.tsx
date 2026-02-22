import type { Metadata } from "next";
import { Providers } from "@/components/Providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "NL2SQL - Natural Language to SQL",
  description: "Convert natural language queries to SQL using AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className="antialiased bg-slate-900 text-slate-100"
      >
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
