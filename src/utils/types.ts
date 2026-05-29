export interface StatConfig {
  name: string;
  min: number;
  max: number;
  default: number;
}

export interface CharacterCreationConfig {
  total_points: number;
  assignable: string[];
}

export interface Choice {
  text: string;
  condition?: Record<string, number>;
  effects?: Record<string, number>;
  next_event: string;
}

export interface EventConfig {
  id: string;
  title: string;
  description?: string;
  descriptionFile?: string;
  choices: Choice[];
}

export interface EndingConfig {
  condition?: Record<string, number>;
  default?: boolean;
  title: string;
  description: string;
}

export interface GameConfig {
  title: string;
  description: string;
  css?: string;
  stats: Record<string, StatConfig>;
  character_creation: CharacterCreationConfig;
  events: EventConfig[];
  endings: EndingConfig[];
}
