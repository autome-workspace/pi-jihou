import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import { usePoll } from "../hooks/usePoll";
import type { VoiceTemplate } from "../types";

const MACROS: { code: string; desc: string }[] = [
  { code: "{{ today() }}", desc: "今日の日付（例: 2026-09-15）" },
  { code: '{{ today("YYYY/MM/DD") }}', desc: "今日の日付（書式指定）" },
  { code: '{{ now("HH:mm") }}', desc: "現在時刻（書式指定）" },
  { code: "{{ year() }}", desc: "現在の年" },
  { code: "{{ month() }}", desc: "現在の月" },
  { code: "{{ day() }}", desc: "現在の日" },
  { code: "{{ weekday() }}", desc: "現在の曜日（0=月曜〜6=日曜）" },
  { code: '{{ days_until("2026-09-15") }}', desc: "指定日までの残り日数" },
  { code: '{{ days_since("2026-04-01") }}', desc: "指定日からの経過日数" },
  { code: "{{ 変数名 }}", desc: "「変数」ページで定義した変数の値" },
];

export default function Voicevox() {
  const { data: status } = usePoll<any>(() => api.get("/api/v1/voicevox/status"), 5000);
  const { data: templates, refresh } = usePoll<VoiceTemplate[]>(
    () => api.get("/api/v1/voice/templates"),
    5000
  );

  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState(true);
  const [name, setName] = useState("");
  const [text, setText] = useState("");
  const [speaker, setSpeaker] = useState(1);
  const [previewResult, setPreviewResult] = useState<{ expanded_text: string; wav_url: string | null } | null>(null);
  const [previewing, setPreviewing] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  function resetForm() {
    setEditingId(null);
    setName("");
    setText("");
    setSpeaker(1);
    setShowForm(false);
  }

  function startEdit(t: VoiceTemplate) {
    setEditingId(t.id);
    setName(t.name);
    setText(t.template_text);
    setSpeaker(t.speaker_id);
    setShowForm(true);
  }

  async function save(e: FormEvent) {
    e.preventDefault();
    const payload = {
      name,
      template_text: text,
      speaker_id: speaker,
      style_id: 0,
      speed: 1.0,
      pitch: 0.0,
      intonation: 1.0,
      volume: 1.0,
      pre_silence_ms: 0,
      post_silence_ms: 0,
      generation_strategy: "before_playback",
    };
    if (editingId) {
      await api.put(`/api/v1/voice/templates/${editingId}`, payload);
    } else {
      await api.post("/api/v1/voice/templates", payload);
    }
    resetForm();
    refresh();
  }

  async function remove(t: VoiceTemplate) {
    await api.del(`/api/v1/voice/templates/${t.id}`);
    refresh();
  }

  async function preview(t: VoiceTemplate) {
    setPreviewing(t.id);
    setPreviewError(null);
    try {
      const res = await api.post<{ expanded_text: string; wav_url: string | null }>(
        `/api/v1/voice/templates/${t.id}/preview`,
        {}
      );
      setPreviewResult(res);
      if (res.wav_url) {
        new Audio(res.wav_url).play().catch(() => {});
      }
    } catch (err) {
      setPreviewError(String(err));
    } finally {
      setPreviewing(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">VOICEVOX</h1>
          <p className="text-sm text-ink-500">
            エンジン:{" "}
            <span className={status?.available ? "text-emerald-700" : "text-red-600"}>
              {status?.available ? `準備完了 (${status.version})` : "利用不可"}
            </span>
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
        >
          + 新規テンプレート
        </button>
      </div>

      {showHelp && (
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <span>テンプレートで使えるマクロと変数</span>
            <button
              className="text-xs text-ink-400 hover:text-ink-600"
              onClick={() => setShowHelp(false)}
            >
              閉じる
            </button>
          </div>
          <div className="px-4 py-3">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-ink-100">
                {MACROS.map((m) => (
                  <tr key={m.code}>
                    <td className="py-1.5 pr-4 font-mono text-ink-800 whitespace-nowrap">{m.code}</td>
                    <td className="py-1.5 text-ink-600">{m.desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-xs text-ink-400">
              変数は「変数」ページで名前と値を登録できます。例: イベント名と日付を登録し、
              「{"{{"} event_name {"}}"}まであと{"{{"} days_until(event_date) {"}}"}日です」のように利用します。
            </p>
          </div>
        </div>
      )}

      {showForm && (
        <form onSubmit={save} className="card p-4 space-y-3">
          <div className="text-sm font-semibold text-ink-700">
            {editingId ? "テンプレートを編集" : "新規テンプレート"}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-ink-500">名前</label>
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <label className="text-xs text-ink-500">話者ID</label>
              <input className="input" type="number" value={speaker} onChange={(e) => setSpeaker(Number(e.target.value))} />
            </div>
          </div>
          <div>
            <label className="text-xs text-ink-500">テンプレート本文（マクロ利用可）</label>
            <textarea className="input" rows={3} value={text} onChange={(e) => setText(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary">{editingId ? "更新" : "保存"}</button>
            <button type="button" className="btn-secondary" onClick={resetForm}>キャンセル</button>
          </div>
        </form>
      )}

      {previewError && <div className="badge-red">{previewError}</div>}

      {previewResult && (
        <div className="card">
          <div className="card-header">プレビュー結果</div>
          <div className="px-4 py-3 space-y-3">
            <div className="text-sm text-ink-700">
              <span className="text-xs text-ink-400 block">展開結果</span>
              {previewResult.expanded_text}
            </div>
            {previewResult.wav_url && (
              <audio controls src={previewResult.wav_url} className="w-full" />
            )}
          </div>
        </div>
      )}

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-ink-500 border-b border-ink-100">
              <th className="px-4 py-2 font-medium">名前</th>
              <th className="px-4 py-2 font-medium">話者</th>
              <th className="px-4 py-2 font-medium">テンプレート</th>
              <th className="px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {(templates ?? []).map((t) => (
              <tr key={t.id}>
                <td className="px-4 py-2 font-medium text-ink-800">{t.name}</td>
                <td className="px-4 py-2 text-ink-600">{t.speaker_id}</td>
                <td className="px-4 py-2 text-ink-600 max-w-md truncate">{t.template_text}</td>
                <td className="px-4 py-2">
                  <div className="flex justify-end gap-1">
                    <button className="btn-secondary" onClick={() => startEdit(t)}>編集</button>
                    <button className="btn-secondary" onClick={() => preview(t)} disabled={previewing === t.id}>
                      {previewing === t.id ? "プレビュー中…" : "プレビュー"}
                    </button>
                    <button className="btn-secondary text-red-600" onClick={() => remove(t)}>削除</button>
                  </div>
                </td>
              </tr>
            ))}
            {(templates ?? []).length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-ink-400">テンプレートはまだありません</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
