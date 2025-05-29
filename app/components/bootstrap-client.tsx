"use client"

import { useEffect } from "react"

export default function BootstrapClient() {
  useEffect(() => {
    // Dynamically import Bootstrap JS only on the client side
    const loadBootstrap = async () => {
      if (typeof window !== "undefined") {
        await import("bootstrap/dist/js/bootstrap.bundle.min.js")
      }
    }

    loadBootstrap()
  }, [])

  return null
}
