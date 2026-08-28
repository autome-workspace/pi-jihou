import { api } from "../api/client";
import { usePoll } from "../hooks/usePoll";
import type { SystemEvent } from "../types";

const LEVEL_BADGE: Record<string, string> = {
  DEBUG: "badge-gray",
  INFO: "badge-green",
  WARNING: "badge-amber",
  ERROR: "badge-red",
};

export default function Logs() {
  const { data: events } = usePoll<SystemEvent[]>(
    () => api.get("/api/v1/system/events?limit=200"),
    5000
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">ログ</h1>
        <p className="text-sm text-ink-500">システムイベントです。</p>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-ink-500 border-b border-ink-100">
              <th className="px-4 py-2 font-medium">時刻</th>
              <th className="px-4 py-2 font-medium">レベル</th>
              <th className="px-4 py-2 font-medium">カテゴリ</th>
              <th className="px-4 py-2 font-medium">メッセージ</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {(events ?? []).map((e) => (
              <tr key={e.id}>
                <td className="px-4 py-2 text-ink-600 whitespace-nowrap">
                  {new Date(e.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-2">
                  <span className={LEVEL_BADGE[e.level] ?? "badge-gray"}>{e.level}</span>
                </td>
                <td className="px-4 py-2 text-ink-600">{e.category}</td>
                <td className="px-4 py-2 text-ink-700">{e.message}</td>
              </tr>
            ))}
            {(events ?? []).length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-ink-400">イベントはありません</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
