export interface Health {
  status: string;
  scheduler: boolean;
  ntp: boolean;
  audio_agent: boolean;
  voicevox: boolean;
}

export interface TimeStatus {
  state: string;
  current_time: string;
  ntp_offset_ms: number;
  last_sync: string | null;
  servers: string[];
}

export interface AudioDevice {
  id: string;
  name: string;
  description: string;
  default: boolean;
}

export interface AudioFile {
  id: string;
  name: string;
  original_filename: string;
  format: string;
  sample_rate: number;
  channels: number;
  bit_depth: number;
  duration_seconds: number;
  size_bytes: number;
  created_at: string;
}

export interface ScheduleRule {
  id?: string;
  rule_type: string;
  time: string | null;
  days_of_week: number[] | null;
  specific_date: string | null;
  cron_expression: string | null;
}

export interface Schedule {
  id: string;
  name: string;
  enabled: boolean;
  volume: number;
  priority: number;
  conflict_policy: string;
  audio_type: string;
  audio_file_id: string | null;
  voice_template_id: string | null;
  rules: ScheduleRule[];
  created_at: string;
  updated_at: string;
}

export interface VoiceTemplate {
  id: string;
  name: string;
  template_text: string;
  speaker_id: number;
  style_id: number;
  speed: number;
  pitch: number;
  intonation: number;
  volume: number;
  pre_silence_ms: number;
  post_silence_ms: number;
  generation_strategy: string;
  created_at: string;
  updated_at: string;
}

export interface VoiceVariable {
  id: string;
  name: string;
  value_type: string;
  value: string;
}

export interface SystemEvent {
  id: string;
  level: string;
  category: string;
  message: string;
  created_at: string;
}
