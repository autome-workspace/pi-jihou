import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import { usePoll } from "../hooks/usePoll";
import type { VoiceVariable } from "../types";

const TYPES: { value: string; label: string }[] = [
  { value: "string", label: "文字列" },
  { value: "integer", label: "整数" },
  { value: "float", label: "小数" },
  { value: "date", label: "日付" },
  { value: "datetime", label: "日時" },
  { value: "boolean", label: "真偽" },
];

const TYPE_LABEL: Record<string, string> = Object.fromEntries(
  TYPES.map((t) => [t.value, t.label])
);

export default function Variables() {
  const { data: variables, refresh } = usePoll<VoiceVariable[]>(
    () => api.get("/api/v1/variables"),
    5000
  );
  const [name, setName] = useState("");
  const [valueType, setValueType] = useState("string");
  const [value, setValue] = useState("");

  async function create(e: FormEvent) {
    e.preventDefault();
    await api.post("/api/v1/variables", { name, value_type: valueType, value });
    setName("");
    setValue("");
    refresh();
  }

  async function remove(v: VoiceVariable) {
    await api.del(`/api/v1/variables/${v.id}`);
    refresh();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">変数</h1>
        <p className="text-sm text-ink-500">VOICEVOXテンプレートで使用するユーザー定義変数です。</p>
      </div>

      <form onSubmit={create} className="card p-4 space-y-3">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-ink-500">名前</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <label className="text-xs text-ink-500">型</label>
            <select className="input" value={valueType} onChange={(e) => setValueType(e.target.value)}>
              {TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-ink-500">値</label>
            <input className="input" value={value} onChange={(e) => setValue(e.target.value)} />
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button type="submit" className="btn-primary">変数を追加</button>
          <p className="text-xs text-ink-400">
            日付は「2026-09-15」、日時は「2026-09-15 12:00:00」の形式で入力してください。テンプレートでは {"{{ 変数名 }}"} で参照できます。
          </p>
        </div>
      </form>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-ink-500 border-b border-ink-100">
              <th className="px-4 py-2 font-medium">名前</th>
              <th className="px-4 py-2 font-medium">型</th>
              <th className="px-4 py-2 font-medium">値</th>
              <th className="px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-100">
            {(variables ?? []).map((v) => (
              <tr key={v.id}>
                <td className="px-4 py-2 font-medium text-ink-800">{v.name}</td>
                <td className="px-4 py-2 text-ink-600">{TYPE_LABEL[v.value_type] ?? v.value_type}</td>
                <td className="px-4 py-2 text-ink-600">{v.value}</td>
                <td className="px-4 py-2">
                  <div className="flex justify-end">
                    <button className="btn-secondary text-red-600" onClick={() => remove(v)}>削除</button>
                  </div>
                </td>
              </tr>
            ))}
            {(variables ?? []).length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-ink-400">変数はまだありません</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
