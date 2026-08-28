# Raspberry Pi スケジュール音声再生システム

Raspberry Pi 4 上で動作する、WebUI から登録したスケジュールに従って音声を自動再生するアプリケーション。

- 通常の音声ファイル（WAV / MP3 / FLAC / OGG / M4A）の再生
- [VOICEVOX](https://voicevox.hiroshiba.jp/) による動的な音声生成（事前生成 + WAV キャッシュ）
- OS 時刻に依存しない、NTP ベースのアプリケーション時刻管理

## アーキテクチャ概要

```text
Browser ──HTTP──> Web Frontend (React + TypeScript + Tailwind)
                      │ REST/WebSocket
                      ▼
                  Backend (FastAPI)
                  ├─ Scheduler
                  ├─ NTP Time Provider
                  ├─ Template Engine
                  └─ Voice Cache Manager
                      │                 │
                      ▼                 ▼
                  SQLite          VOICEVOX ENGINE (Docker)
                      │                 │
                      ▼                 ▼
                  Audio Agent ──> voice cache (WAV)
                  (systemd / PipeWire)
```

## 必要条件

- Raspberry Pi 4（4GB 以上推奨）、microSD または SSD
- Raspberry Pi OS Lite 64-bit（ARM64 / aarch64）
- 音声出力: 3.5mm / HDMI / USB DAC のいずれか

## インストール

```bash
git clone <repository-url>
cd raspi-audio-scheduler
sudo ./install.sh
```

`install.sh` は冪等であり、複数回実行しても安全です。Docker / VOICEVOX を含む一式を自動構築します。

インストール完了後、Web UI にブラウザからアクセスできます。

```text
http://<Raspberry-PiのIPアドレス>/          # Web UI (frontend, port 80)
http://<Raspberry-PiのIPアドレス>:8080      # Backend API (FastAPI)
```

## 更新・アンインストール

```bash
sudo ./update.sh      # 設定バックアップ -> 更新 -> migration -> restart
sudo ./uninstall.sh   # アプリのみ削除（デフォルトではデータを保持）
```

## Firewall

本アプリは標準で `80/tcp`（Web UI）と `8080/tcp`（Backend API）を使用します。
`install.sh` はファイアウォール設定を変更しません。必要に応じて手動で許可してください。

```bash
# ufw の例
sudo ufw allow 80/tcp
sudo ufw allow 8080/tcp
```

外部ネットワークへ公開する場合は認証の導入を必須としてください（Phase 2 で対応予定）。

## ディレクトリ構成

```text
/opt/raspi-audio-scheduler       アプリ本体
/var/lib/raspi-audio-scheduler   データ（audio / voice-cache / database / backups）
/etc/raspi-audio-scheduler       設定（app.env）
/var/log/raspi-audio-scheduler   ログ
```

## 開発

ローカル PC（Raspberry Pi なし）でも `.devcontainer/` を用いて開発できます。
開発環境では音声出力に mock audio backend を利用します。

```bash
docker compose up -d
```

## ライセンス

MIT License
