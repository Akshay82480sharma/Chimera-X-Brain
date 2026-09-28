import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains-mono" });

export const metadata: Metadata = {
  title: "Chimera-X Brain",
  description: "Personal AI Assistant and Memory System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark h-screen overflow-hidden ${inter.variable} ${geist.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <body className="bg-background text-foreground h-screen w-full overflow-hidden flex antialiased" suppressHydrationWarning>
        <Sidebar />
        <div className="flex flex-col flex-1 h-full min-w-0 min-h-0">
          <Header />
          <main className="flex-1 overflow-hidden relative min-h-0">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
