import { useState, ImgHTMLAttributes } from 'react';

/** '/images/flowers/fl-01.jpg' -> '/images/flowers/thumb/fl-01.jpg' (small version for cards and lists). */
export function thumbOf(src: string): string {
  if (!src || !src.startsWith('/images/')) return src;
  const i = src.lastIndexOf('/');
  return `${src.slice(0, i)}/thumb${src.slice(i)}`;
}

/** An <img> that shows a soft branded placeholder instead of a broken-image icon if the file fails to load. */
export function SafeImage({ src, alt, className, ...rest }: ImgHTMLAttributes<HTMLImageElement>) {
  const [failed, setFailed] = useState(false);
  if (failed || !src) {
    return (
      <div
        role="img"
        aria-label={alt}
        className={`${className ?? ''} flex items-center justify-center bg-gradient-to-br from-[#f5ecea] to-[#d7a9a3]/40 dark:from-[#1a0f17] dark:to-[#4a2e3f]/60`}
      >
        <span className="font-serif text-lg tracking-[0.3em] text-[#b88680]/70">SECRET</span>
      </div>
    );
  }
  return <img src={src} alt={alt} className={className} onError={() => setFailed(true)} {...rest} />;
}
