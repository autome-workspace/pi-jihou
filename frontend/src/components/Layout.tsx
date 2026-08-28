import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import {
  Activity,
  AudioLines,
  Clock,
  FileAudio,
  LayoutDashboard,
  ListChecks,
  Mic,
  ScrollText,
  Settings,
  SlidersHorizontal,
} from "lucide-react";

const nav = [
  { to: "/overview", label: "概要", icon: LayoutDashboard },
  { to: "/schedules", label: "スケジュール", icon: ListChecks },
  { to: "/audio", label: "音声ライブラリ", icon: FileAudio },
  { to: "/voicevox", label: "VOICEVOX", icon: Mic },
  { to: "/variables", label: "変数", icon: SlidersHorizontal },
  { to: "/devices", label: "デバイス", icon: AudioLines },
  { to: "/time", label: "時刻", icon: Clock },
  { to: "/logs", label: "ログ", icon: ScrollText },
  { to: "/settings", label: "設定", icon: Settings },
];

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex">
      <aside className="w-56 shrink-0 bg-ink-900 text-ink-300 flex flex-col fixed inset-y-0">
        <div className="h-14 flex items-center gap-2 px-4 border-b border-ink-800">
          <Activity className="w-5 h-5 text-accent" />
          <span className="text-white font-semibold text-sm">音声スケジューラー</span>
        </div>
        <nav className="flex-1 py-2">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-2 text-sm transition-colors ${
                    isActive
                      ? "bg-ink-800 text-white border-l-2 border-accent"
                      : "hover:bg-ink-800 hover:text-white border-l-2 border-transparent"
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
        <div className="px-4 py-3 text-xs text-ink-500 border-t border-ink-800">
          Raspberry Pi Audio Scheduler
        </div>
      </aside>
      <main className="flex-1 ml-56 min-w-0">
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
