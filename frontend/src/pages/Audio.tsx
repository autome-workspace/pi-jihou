import { useState, type ChangeEvent } from "react";
import { api } from "../api/client";
import { usePoll } from "../hooks/usePoll";
import type { AudioFile } from "../types";

export default function Audio() {
  const { data: files, refresh } = usePoll<AudioFile[]>(() => api.get("/api/v1/audio"), 5000);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function upload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("name", file.name.replace(/\.[^.]+$/, ""));
      const res = await fetch("/api/v1/audio", { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function play(a: AudioFile) {
    await api.post(`/api/v1/audio/${a.id}/play`);
  }

  async function remove(a: AudioFile) {
    await api.del(`/api/v1/audio/${a.id}`);
    refresh();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">音声ライブラリ</h1>
          <p className="text-sm text-ink-500">WAV / MP3 / FLAC / OGG / M4A</p>
        </div>
        <label className="btn-primary cursor-pointer">
          {uploading ? "アップロード中…" : "音声をアップロード"}
          <input type="file" accept=".wav,.mp3,.flac,.ogg,.m4a" className="hidden" onChange={upload} disabled={uploading} />
        </label>
      </div>

      {error && <div className="badge-red">{error}</div>}

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-ink-500 border-b border-ink-100">
              <th className="px-4 py-2 font-medium">名前</th>
              <th className="px-4 py-2 font-medium">形式</th>
              <th className="px-4 py-2 font-medium">サンプルレート</th>
              <th className="px-4 py-2 font-medium">長さ</th>
              <th className="px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {(files ?? []).map((a) => (
              <tr key={a.id}>
                <td className="px-4 py-2 font-medium text-ink-800">{a.name}</td>
                <td className="px-4 py-2 text-ink-600">{a.format}</td>
                <td className="px-4 py-2 text-ink-600">{a.sample_rate} Hz</td>
                <td className="px-4 py-2 text-ink-600">{a.duration_seconds.toFixed(1)} 秒</td>
                <td className="px-4 py-2">
                  <div className="flex justify-end gap-1">
                    <button className="btn-secondary" onClick={() => play(a)}>再生</button>
                    <button className="btn-secondary text-red-600" onClick={() => remove(a)}>削除</button>
                  </div>
                </td>
              </tr>
            ))}
            {(files ?? []).length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-ink-400">音声ファイルはまだありません</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
