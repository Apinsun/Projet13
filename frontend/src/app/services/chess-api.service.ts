import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { AdviceResponse } from '../models/chess';

@Injectable({ providedIn: 'root' })
export class ChessApiService {
  private http = inject(HttpClient);
  private baseUrl = '/api/v1';

  getAdvice(fen: string): Observable<AdviceResponse> {
    return this.http.get<AdviceResponse>(
      `${this.baseUrl}/advice/${encodeURIComponent(fen)}`
    );
  }
}
