import { api } from "../api/client";
import { usePoll } from "../hooks/usePoll";
import type { TimeStatus } from "../types";

const STATE_LABEL: Record<string, string> = {
  synchronized: "同期済み",
  degraded: "劣化中",
  unsynchronized: "未同期",
  unknown: "不明",
};

export default function Time() {
  const { data, refresh } = usePoll<TimeStatus>(() => api.get("/api/v1/time/status"), 5000);

  async function sync() {
    await api.post("/api/v1/time/sync");
    refresh();
  }

  const state = data?.state ?? "unknown";
  const badge =
    state === "synchronized" ? "badge-green" : state === "degraded" ? "badge-amber" : "badge-red";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">時刻</h1>
          <p className="text-sm text-ink-500">NTPベースのアプリケーション時刻です。</p>
        </div>
        <button className="btn-secondary" onClick={sync}>今すぐ同期</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">状態</div>
          <div className="px-4 py-4 space-y-3">
            <span className={badge}>{STATE_LABEL[state] ?? state}</span>
            <div className="text-sm text-ink-600">
              現在時刻:{" "}
              <span className="font-medium text-ink-900">
                {data ? new Date(data.current_time).toLocaleString() : "—"}
              </span>
            </div>
            <div className="text-sm text-ink-600">
              NTPオフセット: <span className="font-medium">{data?.ntp_offset_ms ?? 0} ms</span>
            </div>
            <div className="text-sm text-ink-600">
              最終同期:{" "}
              <span className="font-medium">
                {data?.last_sync ? new Date(data.last_sync).toLocaleString() : "未実施"}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">NTPサーバー</div>
          <div className="px-4 py-4">
            <ul className="space-y-2">
              {(data?.servers ?? []).map((s) => (
                <li key={s} className="text-sm text-ink-600">{s}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
