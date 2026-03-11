export interface TeamBoxStats {
  Quads: string;
  L10: string;
  Experience: string;
}

export interface MatchupTableDataType {
  columns: string[];
  teams: {
    name: string;
    stats: { value: string }[];
  }[];
}

export interface UpsetMatchupEntry {
  index: number;
  upset: number;
  factors: string[];
}

export interface UpsetDataType {
  columns: string[];
  regions: { [region: string]: string[] };
  matchups: {
    [matchup: string]: UpsetMatchupEntry;
  };
}

export interface UpsetTableDataType {
  columns: string[];
  values: string[];
}