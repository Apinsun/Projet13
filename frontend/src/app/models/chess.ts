export interface OpeningInfo {
  name: string | null;
  eco: string | null;
}

export interface TheoreticalMove {
  san: string;
  uci: string;
  white: number;
  draws: number;
  black: number;
}

export interface StockfishEvaluation {
  score_cp: number | null;
  mate_in: number | null;
  best_move: string | null;
}

export interface AdviceResponse {
  fen: string;
  opening: OpeningInfo | null;
  theoretical: boolean;
  moves: TheoreticalMove[];
  stockfish_evaluation: StockfishEvaluation | null;
  videos: VideoResult[] | null;
  advice: string;
}

export interface VideoResult {
  title: string;
  url: string;
  channel: string;
  duration: string | null;
  views: string | null;
}

export interface VideoResponse {
  opening: string;
  videos: VideoResult[];
  source: string;
}
