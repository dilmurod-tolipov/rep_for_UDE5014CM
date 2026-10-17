import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  /** 'page' shows a full-screen recovery screen; 'section' hides just the broken part. */
  variant?: 'page' | 'section';
  onReset?: () => void;
}
interface State {
  hasError: boolean;
}

/** Catches rendering errors so one broken part never blanks the whole site on a phone. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[Secret] UI error caught:', error, info.componentStack);
    // For pop-ups: close the broken pop-up (so the page is usable again) and allow it to open next time.
    if (this.props.variant === 'section' && this.props.onReset) {
      this.props.onReset();
      setTimeout(() => this.setState({ hasError: false }), 0);
    }
  }

  reset = () => {
    this.setState({ hasError: false });
    this.props.onReset?.();
  };

  render() {
    if (!this.state.hasError) return this.props.children;
    if (this.props.variant === 'section') return null;
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-5 p-8 text-center bg-[#0c060b] text-[#f5ecea]">
        <div className="font-serif text-3xl tracking-[0.3em] text-[#d7a9a3]">SECRET</div>
        <p className="text-sm opacity-80 max-w-xs">
          Nimadir noto‘g‘ri ketdi. Sahifani yangilang.
          <br />
          Что-то пошло не так. Обновите страницу.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-3 rounded-full bg-[#d7a9a3] text-[#291823] text-sm font-semibold"
        >
          Yangilash / Обновить
        </button>
      </div>
    );
  }
}
