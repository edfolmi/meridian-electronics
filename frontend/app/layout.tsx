import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Meridian Electronics Support",
  description: "Customer support chatbot for Meridian Electronics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

