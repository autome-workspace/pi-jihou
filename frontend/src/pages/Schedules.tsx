import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import { usePoll } from "../hooks/usePoll";
import type { AudioFile, Schedule, VoiceTemplate } from "../types";

const SCHEDULE_TYPES: { value: string; label: string }[] = [
  { value: "daily", label: "毎日" },
  { value: "weekdays", label: "平日" },
  { value: "weekly", label: "曜日指定" },
  { value: "interval", label: "繰り返し（時間内リピート）" },
  { value: "date", label: "指定日" },
  { value: "once", label: "一回" },
  { value: "cron", label: "Cron（上級）" },
];

const CONFLICT_POLICIES: { value: string; label: string }[] = [
  { value: "queue", label: "キュー（再生後に実行）" },
  { value: "interrupt", label: "割り込み（即時実行）" },
  { value: "skip", label: "スキップ" },
];

const WEEKDAYS: { value: number; label: string }[] = [
  { value: 0, label: "月" },
  { value: 1, label: "火" },
  { value: 2, label: "水" },
  { value: 3, label: "木" },
  { value: 4, label: "金" },
  { value: 5, label: "土" },
  { value: 6, label: "日" },
];

const ALL_DAYS = WEEKDAYS.map((d) => d.value);

const TYPE_LABEL: Record<string, string> = Object.fromEntries(
  SCHEDULE_TYPES.map((t) => [t.value, t.label])
);

function emptyRule() {
  return {
    rule_type: "daily",
    time: null,
    start_time: null,
    end_time: null,
    interval_minutes: null,
    days_of_week: null,
    specific_date: null,
    cron_expression: null,
  };
}

export default function Schedules() {
  const { data: schedules, refresh } = usePoll<Schedule[]>(
    () => api.get("/api/v1/schedules"),
    5000
  );
  const { data: audioFiles } = usePoll<AudioFile[]>(() => api.get("/api/v1/audio"), 10000);
  const { data: voiceTemplates } = usePoll<VoiceTemplate[]>(
    () => api.get("/api/v1/voice/templates"),
    10000
  );

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [ruleType, setRuleType] = useState("daily");
  const [time, setTime] = useState("12:00:00");
  const [startTime, setStartTime] = useState("09:00:00");
  const [endTime, setEndTime] = useState("17:00:00");
  const [intervalMinutes, setIntervalMinutes] = useState(10);
  const [selectedDays, setSelectedDays] = useState<number[]>(ALL_DAYS);
  const [audioType, setAudioType] = useState("file");
  const [audioFileId, setAudioFileId] = useState("");
  const [voiceTemplateId, setVoiceTemplateId] = useState("");
  const [volume, setVolume] = useState(80);
  const [conflict, setConflict] = useState("queue");

  function resetForm() {
    setEditingId(null);
    setName("");
    setRuleType("daily");
    setTime("12:00:00");
    setStartTime("09:00:00");
    setEndTime("17:00:00");
    setIntervalMinutes(10);
    setSelectedDays(ALL_DAYS);
    setAudioType("file");
    setAudioFileId("");
    setVoiceTemplateId("");
    setVolume(80);
    setConflict("queue");
    setShowForm(false);
  }

  function startEdit(s: Schedule) {
    const rule = s.rules[0];
    setEditingId(s.id);
    setName(s.name);
    setRuleType(rule?.rule_type ?? "daily");
    setTime(rule?.time ?? "12:00:00");
    setStartTime(rule?.start_time ?? "09:00:00");
    setEndTime(rule?.end_time ?? "17:00:00");
    setIntervalMinutes(rule?.interval_minutes ?? 10);
    setSelectedDays(rule?.days_of_week ?? ALL_DAYS);
    setAudioType(s.audio_type);
    setAudioFileId(s.audio_file_id ?? "");
    setVoiceTemplateId(s.voice_template_id ?? "");
    setVolume(s.volume);
    setConflict(s.conflict_policy);
    setShowForm(true);
  }

  async function save(e: FormEvent) {
    e.preventDefault();
    const rule: Record<string, unknown> = { ...emptyRule(), rule_type: ruleType };
    const daysOfWeek =
      selectedDays.length === ALL_DAYS.length ? null : selectedDays.length ? selectedDays : null;
    rule.days_of_week = daysOfWeek;

    if (ruleType === "interval") {
      rule.start_time = startTime;
      rule.end_time = endTime;
      rule.interval_minutes = Number(intervalMinutes);
    } else {
      rule.time = time;
    }

    const payload = {
      name,
      volume,
      priority: 10,
      conflict_policy: conflict,
      audio_type: audioType,
      audio_file_id: audioType === "file" ? audioFileId || null : null,
      voice_template_id: audioType === "voice" ? voiceTemplateId || null : null,
      rules: [rule],
    };
    if (editingId) {
      await api.put(`/api/v1/schedules/${editingId}`, payload);
    } else {
      await api.post("/api/v1/schedules", payload);
    }
    resetForm();
    refresh();
  }

  function toggleDay(v: number) {
    setSelectedDays((cur) =>
      cur.includes(v) ? cur.filter((d) => d !== v) : [...cur, v]
    );
  }

  async function toggle(s: Schedule) {
    await api.post(`/api/v1/schedules/${s.id}/${s.enabled ? "disable" : "enable"}`);
    refresh();
  }

  async function remove(s: Schedule) {
    await api.del(`/api/v1/schedules/${s.id}`);
    refresh();
  }

  async function run(s: Schedule) {
    await api.post(`/api/v1/schedules/${s.id}/run`);
    refresh();
  }

  const showDays = ruleType === "weekly" || ruleType === "interval";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">スケジュール</h1>
          <p className="text-sm text-ink-500">スケジュールによる音声再生を設定します。</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
        >
          + 新規スケジュール
        </button>
      </div>

      {showForm && (
        <form onSubmit={save} className="card p-4 space-y-3">
          <div className="text-sm font-semibold text-ink-700">
            {editingId ? "スケジュールを編集" : "新規スケジュール"}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-ink-500">名前</label>
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <label className="text-xs text-ink-500">スケジュールタイプ</label>
              <select className="input" value={ruleType} onChange={(e) => setRuleType(e.target.value)}>
                {SCHEDULE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            {ruleType === "interval" ? (
              <>
                <div>
                  <label className="text-xs text-ink-500">開始時刻</label>
                  <input className="input" type="time" step="1" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-ink-500">終了時刻</label>
                  <input className="input" type="time" step="1" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                </div>
                <div>
                  <label className="text-xs text-ink-500">繰り返し間隔（分）</label>
                  <input className="input" type="number" min={0} value={intervalMinutes} onChange={(e) => setIntervalMinutes(Number(e.target.value))} />
                  <p className="text-xs text-ink-400 mt-1">0 を指定すると連続再生（終わり次第すぐ再生）</p>
                </div>
              </>
            ) : (
              <div>
                <label className="text-xs text-ink-500">時刻</label>
                <input className="input" type="time" step="1" value={time} onChange={(e) => setTime(e.target.value)} />
              </div>
            )}

            <div>
              <label className="text-xs text-ink-500">音声種別</label>
              <select className="input" value={audioType} onChange={(e) => setAudioType(e.target.value)}>
                <option value="file">音声ファイル</option>
                <option value="voice">VOICEVOXテンプレート</option>
              </select>
            </div>
            {audioType === "file" ? (
              <div>
                <label className="text-xs text-ink-500">音声ファイル</label>
                <select className="input" value={audioFileId} onChange={(e) => setAudioFileId(e.target.value)}>
                  <option value="">— なし —</option>
                  {(audioFiles ?? []).map((a) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>
            ) : (
              <div>
                <label className="text-xs text-ink-500">VOICEVOXテンプレート</label>
                <select className="input" value={voiceTemplateId} onChange={(e) => setVoiceTemplateId(e.target.value)}>
                  <option value="">— なし —</option>
                  {(voiceTemplates ?? []).map((t) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label className="text-xs text-ink-500">音量 (%)</label>
              <input className="input" type="number" min={0} max={100} value={volume} onChange={(e) => setVolume(Number(e.target.value))} />
            </div>
            <div>
              <label className="text-xs text-ink-500">競合時の動作</label>
              <select className="input" value={conflict} onChange={(e) => setConflict(e.target.value)}>
                {CONFLICT_POLICIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
          </div>

          {showDays && (
            <div>
              <label className="text-xs text-ink-500">対象曜日（全て選択＝毎日）</label>
              <div className="flex flex-wrap gap-2 mt-1">
                {WEEKDAYS.map((d) => (
                  <label key={d.value} className="flex items-center gap-1 text-sm">
                    <input
                      type="checkbox"
                      checked={selectedDays.includes(d.value)}
                      onChange={() => toggleDay(d.value)}
                      className="accent-accent"
                    />
                    {d.label}
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <button type="submit" className="btn-primary">{editingId ? "更新" : "保存"}</button>
            <button type="button" className="btn-secondary" onClick={resetForm}>キャンセル</button>
          </div>
        </form>
      )}

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-ink-500 border-b border-ink-100">
              <th className="px-4 py-2 font-medium">名前</th>
              <th className="px-4 py-2 font-medium">タイプ</th>
              <th className="px-4 py-2 font-medium">時刻</th>
              <th className="px-4 py-2 font-medium">音量</th>
              <th className="px-4 py-2 font-medium">状態</th>
              <th className="px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {(schedules ?? []).map((s) => {
              const rule = s.rules[0];
              const when =
                rule?.rule_type === "interval"
                  ? `${rule.start_time ?? "—"}〜${rule.end_time ?? "—"} / ${
                      rule.interval_minutes === 0 ? "連続再生" : `${rule.interval_minutes ?? "?"}分ごと`
                    }`
                  : rule?.time ?? "—";
              return (
                <tr key={s.id}>
                  <td className="px-4 py-2 font-medium text-ink-800">
                    {s.name}
                    <div className="text-xs font-normal text-ink-400">
                      {s.audio_type === "voice" ? "VOICEVOX" : "音声ファイル"}
                    </div>
                  </td>
                  <td className="px-4 py-2 text-ink-600">
                    {TYPE_LABEL[s.rules[0]?.rule_type ?? ""] ?? s.rules[0]?.rule_type ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-ink-600">{when}</td>
                  <td className="px-4 py-2 text-ink-600">{s.volume}%</td>
                  <td className="px-4 py-2">
                    <span className={s.enabled ? "badge-green" : "badge-gray"}>
                      {s.enabled ? "有効" : "無効"}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex justify-end gap-1">
                      <button className="btn-secondary" onClick={() => startEdit(s)}>編集</button>
                      <button className="btn-secondary" onClick={() => run(s)}>実行</button>
                      <button className="btn-secondary" onClick={() => toggle(s)}>
                        {s.enabled ? "無効化" : "有効化"}
                      </button>
                      <button className="btn-secondary text-red-600" onClick={() => remove(s)}>削除</button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {(schedules ?? []).length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-ink-400">スケジュールはまだありません</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
