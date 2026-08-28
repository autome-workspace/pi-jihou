import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import { usePoll } from "../hooks/usePoll";
import type { AudioFile, Schedule } from "../types";

const SCHEDULE_TYPES: { value: string; label: string }[] = [
  { value: "daily", label: "毎日" },
  { value: "weekdays", label: "平日" },
  { value: "weekly", label: "曜日指定" },
  { value: "date", label: "指定日" },
  { value: "once", label: "一回" },
  { value: "cron", label: "Cron（上級）" },
];

const CONFLICT_POLICIES: { value: string; label: string }[] = [
  { value: "queue", label: "キュー（再生後に実行）" },
  { value: "interrupt", label: "割り込み（即時実行）" },
  { value: "skip", label: "スキップ" },
];

const TYPE_LABEL: Record<string, string> = Object.fromEntries(
  SCHEDULE_TYPES.map((t) => [t.value, t.label])
);

function emptyRule() {
  return { rule_type: "daily", time: "12:00:00", days_of_week: null, specific_date: null, cron_expression: null };
}

export default function Schedules() {
  const { data: schedules, refresh } = usePoll<Schedule[]>(
    () => api.get("/api/v1/schedules"),
    5000
  );
  const { data: audioFiles } = usePoll<AudioFile[]>(() => api.get("/api/v1/audio"), 10000);

  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [ruleType, setRuleType] = useState("daily");
  const [time, setTime] = useState("12:00:00");
  const [audioFileId, setAudioFileId] = useState("");
  const [volume, setVolume] = useState(80);
  const [conflict, setConflict] = useState("queue");

  async function create(e: FormEvent) {
    e.preventDefault();
    await api.post("/api/v1/schedules", {
      name,
      enabled: true,
      volume,
      priority: 10,
      conflict_policy: conflict,
      audio_type: "file",
      audio_file_id: audioFileId || null,
      voice_template_id: null,
      rules: [{ ...emptyRule(), rule_type: ruleType, time }],
    });
    setName("");
    setShowForm(false);
    refresh();
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">スケジュール</h1>
          <p className="text-sm text-ink-500">スケジュールによる音声再生を設定します。</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
          + 新規スケジュール
        </button>
      </div>

      {showForm && (
        <form onSubmit={create} className="card p-4 space-y-3">
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
            <div>
              <label className="text-xs text-ink-500">時刻</label>
              <input className="input" type="time" step="1" value={time} onChange={(e) => setTime(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-ink-500">音声</label>
              <select className="input" value={audioFileId} onChange={(e) => setAudioFileId(e.target.value)}>
                <option value="">— なし —</option>
                {(audioFiles ?? []).map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
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
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">保存</button>
            <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>キャンセル</button>
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
            {(schedules ?? []).map((s) => (
              <tr key={s.id}>
                <td className="px-4 py-2 font-medium text-ink-800">{s.name}</td>
                <td className="px-4 py-2 text-ink-600">
                  {TYPE_LABEL[s.rules[0]?.rule_type ?? ""] ?? s.rules[0]?.rule_type ?? "—"}
                </td>
                <td className="px-4 py-2 text-ink-600">{s.rules[0]?.time ?? "—"}</td>
                <td className="px-4 py-2 text-ink-600">{s.volume}%</td>
                <td className="px-4 py-2">
                  <span className={s.enabled ? "badge-green" : "badge-gray"}>
                    {s.enabled ? "有効" : "無効"}
                  </span>
                </td>
                <td className="px-4 py-2">
                  <div className="flex justify-end gap-1">
                    <button className="btn-secondary" onClick={() => run(s)}>実行</button>
                    <button className="btn-secondary" onClick={() => toggle(s)}>
                      {s.enabled ? "無効化" : "有効化"}
                    </button>
                    <button className="btn-secondary text-red-600" onClick={() => remove(s)}>削除</button>
                  </div>
                </td>
              </tr>
            ))}
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
