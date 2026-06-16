import { useEffect } from 'react'

/**
 * @param {{ trigger: boolean }} props
 */
export default function Confetti({ trigger }) {
  useEffect(() => {
    if (!trigger) return

    console.log('Confetti triggered!')

    // Create container
    const container = document.createElement('div')
    container.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 9999;
    `
    document.body.appendChild(container)

    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52C41A']

    // Create 50 confetti pieces
    for (let i = 0; i < 50; i++) {
      const piece = document.createElement('div')
      const color = colors[Math.floor(Math.random() * colors.length)]
      const left = Math.random() * 100
      const delay = Math.random() * 0.3
      const duration = 2 + Math.random() * 1

      piece.style.cssText = `
        position: absolute;
        width: 10px;
        height: 10px;
        background-color: ${color};
        border-radius: 50%;
        left: ${left}%;
        top: -20px;
        box-shadow: 0 0 6px ${color};
        animation: confetti-fall ${duration}s ease-in forwards;
        animation-delay: ${delay}s;
      `

      container.appendChild(piece)
    }

    // Add center emoji
    const emoji = document.createElement('div')
    emoji.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 60px;
      pointer-events: none;
      z-index: 10000;
      animation: bounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    `
    emoji.textContent = '✨'
    document.body.appendChild(emoji)

    // Clean up
    const cleanupTimer = setTimeout(() => {
      container.remove()
      emoji.remove()
    }, 3000)

    return () => {
      clearTimeout(cleanupTimer)
      try {
        container.remove()
        emoji.remove()
      } catch (e) {
        // Already removed
      }
    }
  }, [trigger])

  return null
}
