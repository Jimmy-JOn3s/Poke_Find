interface CardArtProps {
  imageUrl?: string;
  typeIcon: string;
  gradientFrom: string;
  gradientTo: string;
  alt?: string;
  iconClassName?: string;
  className?: string;
}

export default function CardArt({
  imageUrl,
  typeIcon,
  gradientFrom,
  gradientTo,
  alt = "",
  iconClassName = "text-5xl",
  className = "",
}: CardArtProps) {
  return (
    <>
      <div
        className="absolute inset-0"
        style={{ background: `linear-gradient(160deg, ${gradientFrom}30 0%, ${gradientTo}50 100%)` }}
      />
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={alt}
          className={`relative z-10 h-full w-full object-contain p-2 ${className}`}
          loading="lazy"
        />
      ) : (
        <div
          className={`relative z-10 ${iconClassName}`}
          style={{ filter: "drop-shadow(0 2px 8px rgba(0,0,0,0.6))" }}
        >
          {typeIcon}
        </div>
      )}
    </>
  );
}
