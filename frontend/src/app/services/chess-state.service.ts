import { Injectable, signal } from '@angular/core';
import { AdviceResponse } from '../models/chess';

@Injectable({ providedIn: 'root' })
export class ChessStateService {
  readonly advice = signal<AdviceResponse | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
}
