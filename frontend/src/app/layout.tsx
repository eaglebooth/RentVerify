import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RentVerify",
  description: "AI deposit escrow adjudication on GenLayer",
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
