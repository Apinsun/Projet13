import { Injectable, signal } from '@angular/core';
import { AdviceResponse, VideoResponse } from '../models/chess';

@Injectable({ providedIn: 'root' })
export class ChessStateService {
  readonly advice = signal<AdviceResponse | null>(null);
  readonly videos = signal<VideoResponse | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
}
