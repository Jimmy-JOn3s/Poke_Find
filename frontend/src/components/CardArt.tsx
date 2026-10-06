interface CardArtProps {
  imageUrl?: string;
  typeIcon: string;
  gradientFrom: string;
  gradientTo: string;
  alt?: string;
  iconClassName?: string;
  className?: string;
  /** When true, photo covers the entire container (crop if needed). */
  fill?: boolean;
}

export default function CardArt({
  imageUrl,
  typeIcon,
  gradientFrom,
  gradientTo,
  alt = "",
  iconClassName = "text-5xl",
  className = "",
  fill = false,
}: CardArtProps) {
  const rootClass = fill ? "absolute inset-0 overflow-hidden" : "relative h-full w-full min-h-0";

  return (
    <div className={rootClass}>
      <div
        className="absolute inset-0 z-0"
        style={{ background: `linear-gradient(160deg, ${gradientFrom}30 0%, ${gradientTo}50 100%)` }}
      />
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={alt}
          className={
            fill
              ? `absolute inset-0 z-[1] h-full w-full object-cover ${className}`
              : `relative z-[1] h-full w-full object-contain p-2 ${className}`
          }
          loading="lazy"
        />
      ) : (
        <div
          className={`absolute inset-0 z-[1] flex items-center justify-center ${iconClassName}`}
          style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.6))" }}
        >
          {typeIcon}
        </div>
      )}
    </div>
  );
}
