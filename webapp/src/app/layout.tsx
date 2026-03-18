import type { Metadata, Viewport } from "next";
import "./globals.css";
import { ProfileProvider } from "@/lib/profile-context";
import { BottomNav } from "@/components/bottom-nav";

export const metadata: Metadata = {
  title: "Tu Tru — Biet Menh, Song Chu Dong",
  description:
    "Chon ngay tot dua tren la so Tu Tru ca nhan. Khai truong, cuoi hoi, dong tho, nhap trach.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Tu Tru",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: "#E8E4DF",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body className="antialiased">
        <ProfileProvider>
          <main className="pb-16">{children}</main>
          <BottomNav />
        </ProfileProvider>
      </body>
    </html>
  );
}
