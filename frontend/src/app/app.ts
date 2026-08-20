import { Component, OnInit, inject } from '@angular/core';
import { Subject, debounceTime, switchMap } from 'rxjs';
import { ChessboardComponent } from './components/chessboard/chessboard.component';
import { RecommendationsComponent } from './components/recommendations/recommendations.component';
import { ChessApiService } from './services/chess-api.service';
import { ChessStateService } from './services/chess-state.service';

const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

@Component({
  selector: 'app-root',
  imports: [ChessboardComponent, RecommendationsComponent],
  template: `
    <div class="app-container">
      <header>
        <h1>♟️ Chess Agent FFE</h1>
        <p class="subtitle">Apprentissage des ouvertures assisté par IA</p>
      </header>
      <main>
        <app-chessboard (fenChanged)="onFenChanged($event)"></app-chessboard>
        <app-recommendations></app-recommendations>
      </main>
    </div>
  `,
  styles: `
    .app-container {
      max-width: 1100px;
      margin: 0 auto;
      padding: 20px;
    }
    header {
      margin-bottom: 20px;
    }
    h1 {
      margin: 0;
      font-size: 24px;
      color: #d4d4d4;
    }
    .subtitle {
      margin: 4px 0 0;
      font-size: 13px;
      color: #8a8a8a;
    }
    main {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 20px;
      align-items: start;
    }
    @media (max-width: 900px) {
      main {
        grid-template-columns: 1fr;
      }
    }
  `,
})
export class App implements OnInit {
  private api = inject(ChessApiService);
  private state = inject(ChessStateService);

  private fenSubject = new Subject<string>();

  constructor() {
    this.fenSubject
      .pipe(
        debounceTime(300),
        switchMap((fen) => {
          this.state.loading.set(true);
          this.state.error.set(null);
          return this.api.getAdvice(fen);
        })
      )
      .subscribe({
        next: (res) => {
          this.state.advice.set(res);
          this.state.loading.set(false);
          this.fetchVideos(res.opening?.name);
        },
        error: () => {
          this.state.error.set('Impossible de joindre le backend.');
          this.state.loading.set(false);
        },
      });
  }

  ngOnInit() {
    // Analyse initiale de la position de départ
    this.onFenChanged(STARTING_FEN);
  }

  onFenChanged(fen: string) {
    this.fenSubject.next(fen);
  }

  private fetchVideos(opening: string | null | undefined) {
    if (!opening) {
      this.state.videos.set(null);
      return;
    }
    this.api.getVideos(opening).subscribe({
      next: (v) => this.state.videos.set(v),
      error: () => this.state.videos.set(null),
    });
  }
}
