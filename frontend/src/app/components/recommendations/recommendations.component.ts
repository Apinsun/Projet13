import { Component, computed, inject } from '@angular/core';
import { ChessStateService } from '../../services/chess-state.service';

@Component({
  selector: 'app-recommendations',
  template: `
    <div class="panel">
      <!-- État de chargement -->
      @if (state.loading()) {
        <div class="status">⏳ Analyse de la position…</div>
      }

      <!-- Erreur -->
      @if (state.error()) {
        <div class="status error">❌ {{ state.error() }}</div>
      }

      @if (advice(); as a) {
        <!-- Ouverture -->
        @if (a.opening?.name) {
          <section>
            <h2>📖 Ouverture</h2>
            <div class="opening-name">{{ a.opening.name }}</div>
            @if (a.opening.eco) {
              <div class="opening-eco">ECO {{ a.opening.eco }}</div>
            }
          </section>
        }

        <!-- Coups théoriques -->
        @if (a.moves.length > 0) {
          <section>
            <h2>💡 Coups théoriques</h2>
            <div class="moves">
              @for (m of a.moves.slice(0, 5); track m.san) {
                <div class="move">
                  <span class="move-san">{{ m.san }}</span>
                  <span class="move-stats">{{ winRate(m) }}% vict. · {{ total(m) }} parties</span>
                </div>
              }
            </div>
          </section>
        }

        <!-- Évaluation Stockfish -->
        @if (a.stockfish_evaluation; as eval) {
          <section>
            <h2>⚙️ Évaluation Stockfish</h2>
            <div class="eval">
              @if (eval.mate_in !== null) {
                Mat en {{ eval.mate_in }} coups
              } @else if (eval.score_cp !== null) {
                {{ formatCp(eval.score_cp) }}
              }
              @if (eval.best_move) {
                <div class="best-move">Meilleur coup : {{ eval.best_move }}</div>
              }
            </div>
          </section>
        }

        <!-- Conseil de l'IA -->
        @if (a.advice) {
          <section>
            <h2>🧠 Conseil de l'IA</h2>
            <div class="advice" [innerHTML]="toHtml(a.advice)"></div>
          </section>
        }

        <!-- Vidéos -->
        @if (a.videos?.length) {
          <section>
            <h2>🎥 Vidéos</h2>
            <div class="videos">
              @for (v of a.videos; track v.url) {
                <a class="video" [href]="v.url" target="_blank" rel="noopener">
                  <span class="video-title">{{ v.title }}</span>
                  <span class="video-channel">{{ v.channel }}</span>
                </a>
              }
            </div>
          </section>
        }
      } @else if (!state.loading() && !state.error()) {
        <div class="status">Joue un coup pour commencer l'analyse.</div>
      }
    </div>
  `,
  styles: `
    .panel {
      display: flex;
      flex-direction: column;
      gap: 20px;
      padding: 20px;
      background: #252526;
      border: 1px solid #3c3c3c;
      border-radius: 6px;
      min-height: 460px;
      overflow-y: auto;
    }
    section h2 {
      margin: 0 0 8px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #8a8a8a;
    }
    .status {
      color: #d4d4d4;
      padding: 20px;
      text-align: center;
    }
    .status.error {
      color: #f48771;
    }
    .opening-name {
      font-size: 18px;
      font-weight: 600;
      color: #4ec9b0;
    }
    .opening-eco {
      font-size: 13px;
      color: #8a8a8a;
    }
    .moves {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .move {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #2d2d2d;
      padding: 8px 12px;
      border-radius: 4px;
    }
    .move-san {
      font-weight: 600;
      color: #dcdcaa;
      font-size: 16px;
    }
    .move-stats {
      font-size: 12px;
      color: #8a8a8a;
    }
    .eval {
      color: #d4d4d4;
    }
    .best-move {
      color: #569cd6;
      margin-top: 4px;
      font-size: 13px;
    }
    .advice {
      color: #d4d4d4;
      line-height: 1.6;
      font-size: 14px;
    }
    .videos {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .video {
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: 10px 12px;
      background: #2d2d2d;
      border-radius: 4px;
      text-decoration: none;
      transition: background 0.15s;
    }
    .video:hover {
      background: #3c3c3c;
    }
    .video-title {
      color: #4ec9b0;
      font-size: 14px;
    }
    .video-channel {
      color: #8a8a8a;
      font-size: 12px;
    }
  `,
})
export class RecommendationsComponent {
  readonly state = inject(ChessStateService);
  readonly advice = this.state.advice;

  winRate(m: { white: number; black: number; draws: number }): string {
    const total = m.white + m.black + m.draws;
    return ((m.white / total) * 100).toFixed(0);
  }

  total(m: { white: number; black: number; draws: number }): string {
    return (m.white + m.black + m.draws).toLocaleString('fr-FR');
  }

  formatCp(cp: number): string {
    const side = cp > 0 ? 'Blancs' : cp < 0 ? 'Noirs' : 'neutre';
    return `${cp > 0 ? '+' : ''}${(cp / 100).toFixed(2)} pions (${side})`;
  }

  toHtml(text: string): string {
    return text
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/\[(.+?)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/\n/g, '<br>');
  }
}
