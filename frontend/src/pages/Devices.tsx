import { api } from "../api/client";
import { usePoll } from "../hooks/usePoll";
import type { AudioDevice } from "../types";

export default function Devices() {
  const { data, error, refresh } = usePoll<{ devices: AudioDevice[]; current: string | null }>(
    () => api.get("/api/v1/devices"),
    5000
  );

  async function select(device: AudioDevice) {
    await api.put("/api/v1/devices/current", { id: device.id });
    refresh();
  }

  async function test(device: AudioDevice) {
    await api.post("/api/v1/devices/test", { id: device.id });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">音声デバイス</h1>
        <p className="text-sm text-ink-500">再生に使用する出力デバイスを選択します。</p>
      </div>

      {error && (
        <div className="card border-red-200">
          <div className="px-4 py-3 text-sm text-red-700">
            デバイス情報を取得できませんでした。音声エージェント（Audio Agent）が起動しているか確認してください。
            <div className="mt-1 text-xs text-red-500 break-all">{error}</div>
          </div>
        </div>
      )}

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-ink-500 border-b border-ink-100">
              <th className="px-4 py-2 font-medium">デバイス</th>
              <th className="px-4 py-2 font-medium">説明</th>
              <th className="px-4 py-2 font-medium">状態</th>
              <th className="px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {(data?.devices ?? []).map((d) => (
              <tr key={d.id}>
                <td className="px-4 py-2 font-medium text-ink-800">{d.name}</td>
                <td className="px-4 py-2 text-ink-600 truncate max-w-md">{d.description}</td>
                <td className="px-4 py-2">
                  <span className={d.id === data?.current ? "badge-green" : "badge-gray"}>
                    {d.id === data?.current ? "使用中" : "待機"}
                  </span>
                </td>
                <td className="px-4 py-2">
                  <div className="flex justify-end gap-1">
                    <button className="btn-secondary" onClick={() => test(d)}>音声テスト</button>
                    {d.id !== data?.current && (
                      <button className="btn-primary" onClick={() => select(d)}>選択</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {(data?.devices ?? []).length === 0 && !error && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-ink-400">
                  音声デバイスが見つかりません
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
