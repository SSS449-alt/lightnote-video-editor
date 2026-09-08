import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LightnoteAI — AI Video Editor",
  description: "Edit videos with natural language.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        style={{
          backgroundColor: "#0a0a0f",
          color: "#f1f1f5",
          minHeight: "100vh",
          fontFamily: "Inter, system-ui, sans-serif",
        }}
      >
        {children}
      </body>
    </html>
  );
}