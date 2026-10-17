// Web Audio API Synthesizer for ambient soundscapes and micro-interactions
// Maison Secret Haute Floristique Soundscape: French Luxury Harp & Glass Celesta
// Operates 100% locally with zero external network audio assets or file dependencies

class SoundManager {
  private ctx: AudioContext | null = null;
  private ambientGain: GainNode | null = null;
  private ambientOscs: OscillatorNode[] = [];
  private lfo: OscillatorNode | null = null;
  private harpTimer: ReturnType<typeof setInterval> | null = null;
  private isAmbientPlaying = false;
  private soundEffectsEnabled = false;

  private getAudioContext(): AudioContext | null {
    if (typeof window === 'undefined') return null;

    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtx) {
        try {
          this.ctx = new AudioCtx();
        } catch {
          // Some phones refuse to create an audio context (limits, power saving). Sound is optional.
          this.ctx = null;
        }
      }
    }
    return this.ctx;
  }

  public async resumeContext(): Promise<AudioContext | null> {
    const ctx = this.getAudioContext();
    if (!ctx) return null;

    if (ctx.state === 'suspended') {
      try {
        await ctx.resume();
      } catch (err) {
        console.warn('AudioContext resume was postponed:', err);
      }
    }
    return ctx;
  }

  public async toggleAmbientSound(enable?: boolean): Promise<boolean> {
    const ctx = await this.resumeContext();
    if (!ctx) return false;

    const shouldEnable = enable !== undefined ? enable : !this.isAmbientPlaying;

    if (shouldEnable) {
      if (this.isAmbientPlaying) return true;

      try {
        if (ctx.state !== 'running') {
          await ctx.resume();
        }

        const now = ctx.currentTime;

        // Master ambient bus with smooth swell
        const masterGain = ctx.createGain();
        masterGain.gain.setValueAtTime(0.001, now);
        masterGain.gain.linearRampToValueAtTime(0.14, now + 1.6);

        // Warm French boutique acoustic lowpass filter
        const filter = ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(520, now);
        filter.Q.setValueAtTime(1.8, now);

        // Very slow, soothing breathing LFO (modulating warm acoustic space)
        const lfo = ctx.createOscillator();
        lfo.type = 'sine';
        lfo.frequency.setValueAtTime(0.1, now); // 10 second tranquil breathing swell

        const lfoGain = ctx.createGain();
        lfoGain.gain.setValueAtTime(140, now);
        lfo.connect(lfoGain);
        lfoGain.connect(filter.frequency);
        lfo.start();

        // Lush Rose-Garden Warm Chord: D Major 9th / F# minor 7 (F#2, A2, C#3, F#3, A3)
        // Tuned for warm tranquility and opulent relaxation
        const chordFrequencies = [92.5, 110.0, 138.59, 185.0, 220.0];
        const oscs: OscillatorNode[] = [];

        chordFrequencies.forEach((freq, idx) => {
          const osc = ctx.createOscillator();
          osc.type = idx % 2 === 0 ? 'sine' : 'triangle';
          // Micro-tuning creates a lush, organic ensemble shimmer
          const microDetune = (idx - 2) * 0.45;
          osc.frequency.setValueAtTime(freq + microDetune, now);

          const voiceGain = ctx.createGain();
          voiceGain.gain.setValueAtTime(0.22 / (idx + 1), now);

          osc.connect(voiceGain);
          voiceGain.connect(filter);
          osc.start();
          oscs.push(osc);
        });

        filter.connect(masterGain);
        masterGain.connect(ctx.destination);

        this.ambientGain = masterGain;
        this.ambientOscs = oscs;
        this.lfo = lfo;
        this.isAmbientPlaying = true;

        // Generative Wind-Harp & Crystal Celesta Melody Loop
        // Plays delicate, romantic cascading harp notes every 4-6 seconds
        if (this.harpTimer) clearInterval(this.harpTimer);
        
        // Initial soft welcoming harp chime
        setTimeout(() => {
          if (this.isAmbientPlaying) {
            this.playGlassHarpSequence([554.37, 739.99, 880.0, 1108.73]);
          }
        }, 500);

        this.harpTimer = setInterval(() => {
          if (this.isAmbientPlaying) {
            // Ethereal pentatonic motifs: F# minor / A major pentatonic
            const motifs = [
              [554.37, 739.99, 880.0, 1108.73], // C#5 -> F#5 -> A5 -> C#6
              [739.99, 880.0, 1108.73, 1318.51], // F#5 -> A5 -> C#6 -> E6
              [1108.73, 880.0, 739.99, 554.37], // Cascading petal fall
              [659.25, 739.99, 987.77, 1318.51], // Warm sunset bloom
            ];
            const chosen = motifs[Math.floor(Math.random() * motifs.length)];
            this.playGlassHarpSequence(chosen);
          }
        }, 5200);

        return true;
      } catch (err) {
        console.error('Error starting ambient soundscape:', err);
        this.isAmbientPlaying = false;
        return false;
      }
    } else {
      // Gracefully fade out
      if (this.ambientGain && ctx) {
        try {
          const now = ctx.currentTime;
          this.ambientGain.gain.linearRampToValueAtTime(0.0001, now + 0.6);

          if (this.harpTimer) {
            clearInterval(this.harpTimer);
            this.harpTimer = null;
          }

          setTimeout(() => {
            try {
              this.ambientOscs.forEach((osc) => {
                try {
                  osc.stop();
                  osc.disconnect();
                } catch {
                  /* ignore */
                }
              });
              this.ambientOscs = [];
              if (this.lfo) {
                try {
                  this.lfo.stop();
                  this.lfo.disconnect();
                } catch {
                  /* ignore */
                }
                this.lfo = null;
              }
              if (this.ambientGain) {
                try {
                  this.ambientGain.disconnect();
                } catch {
                  /* ignore */
                }
                this.ambientGain = null;
              }
            } catch {
              // ignore
            }
          }, 700);
        } catch {
          // ignore
        }
      }

      this.isAmbientPlaying = false;
      return false;
    }
  }

  public getIsAmbientPlaying(): boolean {
    return this.isAmbientPlaying;
  }

  // Plays a delicate sequence of crystalline harp tones
  private playGlassHarpSequence(frequencies: number[]): void {
    const ctx = this.getAudioContext();
    if (!ctx || ctx.state !== 'running') return;

    frequencies.forEach((freq, idx) => {
      setTimeout(() => {
        if (!this.isAmbientPlaying || !this.ctx) return;
        this.playGlassTone(freq, 0.045, 1.4);
      }, idx * 160);
    });
  }

  // Dual-oscillator FM glass/bell synthesis
  private playGlassTone(freq: number, volume = 0.05, decay = 1.2): void {
    const ctx = this.getAudioContext();
    if (!ctx) return;

    try {
      if (ctx.state === 'suspended') {
        ctx.resume();
      }
      const now = ctx.currentTime;

      // Carrier
      const carrier = ctx.createOscillator();
      carrier.type = 'sine';
      carrier.frequency.setValueAtTime(freq, now);

      // Modulator for glass shimmer
      const modulator = ctx.createOscillator();
      modulator.type = 'sine';
      modulator.frequency.setValueAtTime(freq * 2.76, now); // Harmonic ratio for crystal chime

      const modGain = ctx.createGain();
      modGain.gain.setValueAtTime(freq * 0.35, now);
      modGain.gain.exponentialRampToValueAtTime(0.01, now + decay * 0.5);

      modulator.connect(modGain);
      modGain.connect(carrier.frequency);

      // Volume envelope
      const gain = ctx.createGain();
      gain.gain.setValueAtTime(volume, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + decay);

      carrier.connect(gain);
      gain.connect(ctx.destination);

      carrier.start(now);
      modulator.start(now);
      carrier.stop(now + decay);
      modulator.stop(now + decay);
    } catch {
      // ignore
    }
  }

  // Micro-interaction: Luxury Glass Chime
  public playChime(freq = 987.77, volume = 0.07): void {
    if (!this.soundEffectsEnabled) return;
    this.playGlassTone(freq, volume, 1.0);
  }

  // Micro-interaction: Delicate Acoustic Harp Pluck
  public playPluck(): void {
    if (!this.soundEffectsEnabled) return;
    const ctx = this.getAudioContext();
    if (!ctx) return;

    try {
      if (ctx.state === 'suspended') {
        ctx.resume();
      }
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(587.33, now); // D5
      osc.frequency.exponentialRampToValueAtTime(739.99, now + 0.08); // F#5 glide

      gain.gain.setValueAtTime(0.09, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.35);
    } catch {
      // ignore
    }
  }

  // Micro-interaction: Elegant Flourish
  public playSuccessChord(): void {
    const ctx = this.getAudioContext();
    if (!ctx) return;

    try {
      if (ctx.state === 'suspended') {
        ctx.resume();
      }
      // D Major 9th flourish (D5, F#5, A5, C#6)
      const notes = [587.33, 739.99, 880.0, 1108.73];
      notes.forEach((freq, index) => {
        setTimeout(() => {
          this.playGlassTone(freq, 0.065, 1.2);
        }, index * 90);
      });
    } catch {
      // ignore
    }
  }

  // Micro-interaction: Soft Rosewood Click
  public playTick(): void {
    if (!this.soundEffectsEnabled) return;
    const ctx = this.getAudioContext();
    if (!ctx) return;

    try {
      if (ctx.state === 'suspended') {
        ctx.resume();
      }
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(1180, now);
      osc.frequency.exponentialRampToValueAtTime(800, now + 0.03);

      gain.gain.setValueAtTime(0.035, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.035);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.035);
    } catch {
      // ignore
    }
  }
}

export const soundManager = new SoundManager();
