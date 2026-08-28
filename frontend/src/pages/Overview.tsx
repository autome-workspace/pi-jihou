import { usePoll } from "../hooks/usePoll";
import { api } from "../api/client";
import type { Health, TimeStatus } from "../types";

const STATE_LABEL: Record<string, string> = {
  synchronized: "同期済み",
  degraded: "劣化中",
  unsynchronized: "未同期",
  unknown: "不明",
};

function StatusRow({ label, ok, detail }: { label: string; ok: boolean; detail: string }) {
  return (
    <div className="flex items-center justify-between py-2.5">
      <span className="text-sm text-ink-600">{label}</span>
      <span className="flex items-center gap-2">
        <span className={`dot ${ok ? "bg-emerald-500" : "bg-red-500"}`} />
        <span className={`text-sm font-medium ${ok ? "text-emerald-700" : "text-red-600"}`}>
          {detail}
        </span>
      </span>
    </div>
  );
}

export default function Overview() {
  const { data: health } = usePoll<Health>(
    () => api.get("/api/v1/system/health"),
    5000
  );
  const { data: time } = usePoll<TimeStatus>(
    () => api.get("/api/v1/time/status"),
    5000
  );
  const { data: next } = usePoll<any>(
    () => api.get("/api/v1/system/next-playback"),
    5000
  );
  const { data: history } = usePoll<any[]>(
    () => api.get("/api/v1/system/history?limit=10"),
    5000
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">概要</h1>
        <p className="text-sm text-ink-500">システム状態の概要です。</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">システム状態</div>
          <div className="px-4 py-2 divide-y divide-ink-100">
            <StatusRow
              label="スケジューラー"
              ok={health?.scheduler ?? false}
              detail={health?.scheduler ? "実行中" : "停止中"}
            />
            <StatusRow
              label="時刻同期"
              ok={time?.state === "synchronized"}
              detail={STATE_LABEL[time?.state ?? "unknown"] ?? time?.state ?? "不明"}
            />
            <StatusRow
              label="VOICEVOX"
              ok={health?.voicevox ?? false}
              detail={health?.voicevox ? "準備完了" : "利用不可"}
            />
            <StatusRow
              label="音声出力"
              ok={health?.audio_agent ?? false}
              detail={health?.audio_agent ? "接続済み" : "利用不可"}
            />
          </div>
        </div>

        <div className="card">
          <div className="card-header">次の再生</div>
          <div className="px-4 py-4">
            {next ? (
              <div className="space-y-2">
                <div className="text-2xl font-semibold text-ink-900">
                  {new Date(next.scheduled_at).toLocaleTimeString()}
                </div>
                <div className="text-sm text-ink-600">{next.name}</div>
              </div>
            ) : (
              <div className="text-sm text-ink-500">予定されているスケジュールはありません</div>
            )}
          </div>
          <div className="border-t border-ink-100 px-4 py-2 text-xs text-ink-500">
            現在のアプリケーション時刻:{" "}
            {time ? new Date(time.current_time).toLocaleString() : "—"}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">最近の再生履歴</div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink-500 border-b border-ink-100">
                <th className="px-4 py-2 font-medium">予定</th>
                <th className="px-4 py-2 font-medium">開始</th>
                <th className="px-4 py-2 font-medium">遅延</th>
                <th className="px-4 py-2 font-medium">結果</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-100">
              {(history ?? []).map((h) => (
                <tr key={h.id}>
                  <td className="px-4 py-2 text-ink-600">
                    {h.scheduled_at ? new Date(h.scheduled_at).toLocaleTimeString() : "—"}
                  </td>
                  <td className="px-4 py-2 text-ink-600">
                    {h.started_at ? new Date(h.started_at).toLocaleTimeString() : "—"}
                  </td>
                  <td className="px-4 py-2 text-ink-600">
                    {h.delay_ms != null ? `+${Math.round(h.delay_ms)} ms` : "—"}
                  </td>
                  <td className="px-4 py-2">
                    <span
                      className={
                        h.result === "success" ? "badge-green" : "badge-red"
                      }
                    >
                      {h.result === "success" ? "成功" : "失敗"}
                    </span>
                  </td>
                </tr>
              ))}
              {(history ?? []).length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-ink-400">
                    再生履歴はまだありません
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
