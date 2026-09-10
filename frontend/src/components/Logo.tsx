export function Logo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      role="img"
      aria-label="Airspace Copilot"
    >
      <defs>
        <linearGradient
          id="logo-plane"
          x1="7"
          y1="6"
          x2="26"
          y2="20"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#FFD166" />
          <stop offset="1" stopColor="#FF8A3D" />
        </linearGradient>
      </defs>

      {}
      <rect x="4" y="21.5" width="15" height="3.6" rx="1.8" fill="#A78BFA" opacity="0.85" />
      <rect x="11" y="26.4" width="17" height="3.2" rx="1.6" fill="#FDE047" opacity="0.7" />

      {}
      <path
        d="M27 3.4 4.6 13.2a1 1 0 0 0 .07 1.85l6.2 2.2 15.9-13.6a.4.4 0 0 1 .55.6L14.1 18.9l.55 6.5a1 1 0 0 0 1.77.56l3.3-4.1 4.9 1.74a1 1 0 0 0 1.31-.78L28.5 4.5a1 1 0 0 0-1.5-1.1z"
        fill="url(#logo-plane)"
      />
      <path
        d="m11.9 17.3 2.2 1.6.55 6.5a1 1 0 0 0 1.77.56l3.3-4.1-7.82-4.56z"
        fill="#E8622B"
        opacity="0.55"
      />
    </svg>
  );
}
