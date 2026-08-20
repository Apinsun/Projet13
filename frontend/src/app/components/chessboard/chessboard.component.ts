import { Component, EventEmitter, Output, ViewChild } from '@angular/core';
import { NgxChessBoardModule } from 'ngx-chess-board';
import { NgxChessBoardView, MoveChange } from 'ngx-chess-board';

@Component({
  selector: 'app-chessboard',
  imports: [NgxChessBoardModule],
  template: `
    <div class="board-wrapper">
      <ngx-chess-board
        #board
        [size]="460"
        [darkTileColor]="'#769656'"
        [lightTileColor]="'#eeeed2'"
        [showCoords]="true"
        (moveChange)="onMoveChange($event)"
      ></ngx-chess-board>

      <div class="board-actions">
        <button (click)="reset()">↺ Reset</button>
        <button (click)="undo()">↶ Undo</button>
      </div>
    </div>
  `,
  styles: `
    .board-wrapper {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .board-actions {
      display: flex;
      gap: 8px;
    }
    button {
      background: #333;
      color: #d4d4d4;
      border: 1px solid #444;
      border-radius: 4px;
      padding: 8px 16px;
      cursor: pointer;
      font-size: 14px;
    }
    button:hover {
      background: #3c3c3c;
    }
  `,
})
export class ChessboardComponent {
  @ViewChild('board') board!: NgxChessBoardView;
  @Output() fenChanged = new EventEmitter<string>();

  reset() {
    this.board.reset();
    this.emitFen();
  }

  undo() {
    this.board.undo();
    this.emitFen();
  }

  onMoveChange(change: MoveChange) {
    this.fenChanged.emit(change.fen);
  }

  private emitFen() {
    this.fenChanged.emit(this.board.getFEN());
  }
}
