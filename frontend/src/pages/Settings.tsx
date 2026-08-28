import { api } from "../api/client";
import { usePoll } from "../hooks/usePoll";

export default function Settings() {
  const { data, refresh } = usePoll<Record<string, string>>(
    () => api.get("/api/v1/settings"),
    5000
  );

  async function save(key: string, value: string) {
    await api.put(`/api/v1/settings/${key}`, { value });
    refresh();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">設定</h1>
        <p className="text-sm text-ink-500">アプリケーション設定です。</p>
      </div>

      <div className="card">
        <div className="card-header">設定</div>
        <div className="px-4 py-2 divide-y divide-ink-100">
          {Object.entries(data ?? {}).map(([key, value]) => (
            <div key={key} className="flex items-center gap-3 py-2">
              <div className="w-48 text-sm text-ink-600 truncate">{key}</div>
              <input
                className="input flex-1"
                defaultValue={value}
                onBlur={(e) => save(key, e.target.value)}
              />
            </div>
          ))}
          {Object.keys(data ?? {}).length === 0 && (
            <div className="py-4 text-sm text-ink-400">保存された設定はありません</div>
          )}
        </div>
      </div>
    </div>
  );
}
