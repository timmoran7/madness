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

export interface CompactMatchupDataType {
  columns: string[];
  regions: {
    [region: string]: {
      [matchup: string]: (string | string[])[][];
    };
  };
}

export interface CompactUpsetTableDataType {
  columns: string[];
  matchups: {
    [matchup: string]: string[];
  };
}

export interface UpsetTableDataType {
  columns: string[];
  values: string[];
}