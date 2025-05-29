import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import "bootstrap/dist/css/bootstrap.min.css"
import Navigation from "./components/navigation"
import Footer from "./components/footer"
import BootstrapClient from "./components/bootstrap-client"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "SasaBot Technologies - Smarter Business Starts Here",
  description:
    "AI-powered automation solutions for modern enterprises. Business intelligence, HR automation, payroll processing, and process automation.",
  keywords: "AI automation, business intelligence, HR automation, payroll processing, SasaBot Technologies",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Navigation />
        <main>{children}</main>
        <Footer />
        <BootstrapClient />
      </body>
    </html>
  )
}
