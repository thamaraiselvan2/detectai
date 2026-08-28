import { useEffect, useState } from 'react'
import './SecuritySplash.css'

const SPLASH_DURATION = 4000
const FADE_DURATION = 700

export default function SecuritySplash() {
  const [showSplash, setShowSplash] = useState(true)
  const [isFading, setIsFading] = useState(false)

  useEffect(() => {
    const fadeTimer = setTimeout(() => setIsFading(true), SPLASH_DURATION - FADE_DURATION)
    const removeTimer = setTimeout(() => setShowSplash(false), SPLASH_DURATION)

    return () => {
      clearTimeout(fadeTimer)
      clearTimeout(removeTimer)
    }
  }, [])

  if (!showSplash) return null

  return (
    <div className={`security-splash${isFading ? ' security-splash--fading' : ''}`} aria-hidden="true">
      <div className="security-splash__image" />
      <div className="security-splash__shade" />
      <div className="security-splash__grid" />
      <div className="security-splash__scan" />
      <div className="security-splash__particles" />
      <div className="security-splash__glow" />
    </div>
  )
}
