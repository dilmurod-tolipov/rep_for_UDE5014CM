import { ReactNode, useEffect } from 'react';
import { CheckCircle2, CircleDot, Clock, Package, Truck, XCircle, BadgeCheck } from 'lucide-react';
import { Language, OrderStatus } from '../types';
import { STATUS_LABEL, STATUS_STYLE } from './i18n';

const STATUS_ICON: Record<OrderStatus, typeof Clock> = {
  new: CircleDot, confirmed: BadgeCheck, assembling: Package, quality_check: Package, in_transit: Truck, delivered: CheckCircle2, cancelled: XCircle
};

/** Status is never shown by colour alone: icon + text label + colour. */
export function StatusBadge({ status, lang }: { status: OrderStatus; lang: Language }) {
  const Icon = STATUS_ICON[status];
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[11px] font-semibold whitespace-nowrap ${STATUS_STYLE[status]}`}>
      <Icon className="w-3 h-3" aria-hidden="true" />
      {STATUS_LABEL[lang][status]}
    </span>
  );
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-white/10 bg-[#171016] ${className}`}>{children}</div>;
}

export function Button({
  children, onClick, variant = 'ghost', type = 'button', disabled, className = ''
}: { children: ReactNode; onClick?: () => void; variant?: 'primary' | 'ghost' | 'danger'; type?: 'button' | 'submit'; disabled?: boolean; className?: string }) {
  const styles = {
    primary: 'bg-[#d7a9a3] text-[#291823] hover:bg-[#e2bbb6]',
    ghost: 'bg-white/5 text-neutral-200 hover:bg-white/10 border border-white/10',
    danger: 'bg-red-500/10 text-red-300 hover:bg-red-500/20 border border-red-500/30'
  }[variant];
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-1.5 min-h-[40px] px-4 rounded-xl text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer ${styles} ${className}`}
    >
      {children}
    </button>
  );
}

/** Bottom sheet on phones, centred panel on larger screens. Closes on Escape and backdrop tap. */
export function Sheet({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title: string; children: ReactNode; wide?: boolean }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center" role="dialog" aria-modal="true" aria-label={title}>
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <div className={`relative w-full ${wide ? 'sm:max-w-3xl' : 'sm:max-w-xl'} max-h-[92dvh] overflow-y-auto overscroll-contain bg-[#120b10] border border-white/10 rounded-t-3xl sm:rounded-3xl shadow-2xl`}>
        <div className="sticky top-0 z-10 flex items-center justify-between gap-3 px-5 py-4 bg-[#120b10]/95 border-b border-white/10">
          <h2 className="font-serif text-xl text-white truncate">{title}</h2>
          <button onClick={onClose} className="min-w-[40px] min-h-[40px] rounded-full bg-white/5 hover:bg-white/10 text-neutral-300 cursor-pointer" aria-label="Close">
            ✕
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

/** In-page confirmation (no browser pop-ups, which phones handle badly). */
export function Confirm({ open, text, confirmLabel, cancelLabel, onConfirm, onCancel, danger }: {
  open: boolean; text: string; confirmLabel: string; cancelLabel: string; onConfirm: () => void; onCancel: () => void; danger?: boolean;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4" role="alertdialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/70" onClick={onCancel} />
      <div className="relative w-full max-w-sm rounded-2xl bg-[#171016] border border-white/10 p-5 shadow-2xl">
        <p className="text-sm text-neutral-200 mb-5 leading-relaxed">{text}</p>
        <div className="flex gap-2 justify-end">
          <Button onClick={onCancel}>{cancelLabel}</Button>
          <Button variant={danger ? 'danger' : 'primary'} onClick={onConfirm}>{confirmLabel}</Button>
        </div>
      </div>
    </div>
  );
}
