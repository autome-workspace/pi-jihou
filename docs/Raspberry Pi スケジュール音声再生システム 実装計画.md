# Raspberry Pi スケジュール音声再生システム 実装計画

## 1. プロジェクト概要

Raspberry Pi 4を利用し、WebUIから登録したスケジュールに従って音声を自動再生するアプリケーションを開発する。

通常のWAV/MP3等の音声ファイルに加えてVOICEVOXによる動的な音声生成に対応する。

VOICEVOXによる音声生成はRaspberry Pi 4では一定の処理時間を要する可能性があるため、再生予定時刻より前に音声を生成し、WAVキャッシュとして保存する。

OS時刻だけには依存せず、アプリケーション自身がNTPサーバーから取得した時刻を基準としてスケジュールを管理する。

---

# 2. 想定環境

## ハードウェア

- Raspberry Pi 4
- 4GB以上推奨
- microSDまたはSSD
- Ethernet推奨
- Wi-Fiにも対応
- 音声出力
  - Raspberry Pi 3.5mm
  - HDMI
  - USB DAC

## OS

Raspberry Pi OS Lite 64-bitを基本とする。

GUI環境は不要。

## アーキテクチャ

ARM64 / aarch64を正式サポート対象とする。

---

# 3. システム構成

```text
Browser
   │
   │ HTTP
   ▼
┌─────────────────────┐
│ Web Frontend        │
│ React + TypeScript  │
│ Tailwind CSS        │
└─────────┬───────────┘
          │ REST/WebSocket
          ▼
┌─────────────────────┐
│ Backend             │
│ FastAPI             │
│                     │
│ API                 │
│ Scheduler           │
│ NTP Time Provider   │
│ Template Engine     │
│ Voice Cache Manager │
└──────┬────────┬─────┘
       │        │
       │        └──────────────┐
       ▼                       ▼
┌────────────┐          ┌──────────────┐
│ SQLite     │          │ VOICEVOX     │
│ Database   │          │ ENGINE       │
└────────────┘          │ Docker       │
                        └──────┬───────┘
                               │
                          WAV生成
                               │
                               ▼
                         voice cache

Backend
   │
   │ local IPC / HTTP
   ▼
┌────────────────────────┐
│ Audio Agent            │
│ systemd service        │
│                        │
│ PipeWire / ALSA        │
└──────────┬─────────────┘
           │
       ┌───┼─────────┐
       ▼   ▼         ▼
     3.5mm HDMI    USB DAC
```

---

# 4. 技術スタック

## Backend

- Python 3.11+
- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- Pydantic
- httpx
- asyncio

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Lucide Icons

## Database

SQLite

将来PostgreSQLへ移行可能な設計にする。

## Audio

基本的にはPipeWireを使用する。

デバイス列挙・選択には以下を利用する。

- `wpctl`
- `pw-cli`
- 必要に応じて`pactl`

音声変換：

- ffmpeg

## VOICEVOX

VOICEVOX ENGINE ARM64 CPU版をDockerコンテナとして実行する。

## Deployment

- Docker Compose
- systemd
- install.sh

---

# 5. リポジトリ構成

```text
raspi-audio-scheduler/
│
├── README.md
├── LICENSE
├── .env.example
├── compose.yml
├── install.sh
├── uninstall.sh
├── update.sh
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   │
│   └── app/
│       ├── main.py
│       │
│       ├── api/
│       │   ├── schedules.py
│       │   ├── audio.py
│       │   ├── voicevox.py
│       │   ├── devices.py
│       │   ├── time.py
│       │   ├── settings.py
│       │   └── system.py
│       │
│       ├── scheduler/
│       │   ├── scheduler.py
│       │   ├── rules.py
│       │   └── executor.py
│       │
│       ├── time/
│       │   ├── ntp_client.py
│       │   ├── time_provider.py
│       │   └── clock_monitor.py
│       │
│       ├── voice/
│       │   ├── voicevox.py
│       │   ├── template.py
│       │   ├── macros.py
│       │   ├── cache.py
│       │   └── prefetch.py
│       │
│       ├── audio/
│       │   ├── client.py
│       │   └── normalization.py
│       │
│       ├── models/
│       ├── schemas/
│       ├── database/
│       └── services/
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│
├── audio-agent/
│   ├── pyproject.toml
│   ├── audio_agent/
│   └── raspi-audio-agent.service
│
├── deploy/
│   ├── systemd/
│   ├── nginx/
│   └── config/
│
├── scripts/
│   ├── detect-audio.sh
│   ├── migrate.sh
│   └── healthcheck.sh
│
├── data/
│   ├── audio/
│   ├── voice-cache/
│   ├── database/
│   └── backups/
│
└── tests/
```

`data/`はGit管理対象外とする。

---

# 6. WebUI

Cloudflare Dashboardに近いデザインとする。

ただし完全なコピーではなく、

- 白背景
- 薄いグレーのカード
- 濃紺系テキスト
- オレンジ系アクセント
- 左側固定ナビゲーション
- シンプルなテーブル
- 小さめのborder-radius
- status badge

を基本とする。

---

# 7. WebUI画面

## Overview

表示項目：

- Scheduler status
- NTP status
- VOICEVOX status
- Audio output
- Next playback
- Current application time
- 最近の再生履歴
- VOICEVOX生成キュー

例：

```text
System Status

Scheduler       ● Running
Time Sync       ● Synchronized
VOICEVOX        ● Ready
Audio           ● USB DAC

Next Playback

17:00
Closing Announcement
in 2h 13m
```

---

# 8. Schedule画面

登録可能項目：

- 名前
- 有効/無効
- 再生時刻
- スケジュールタイプ
- 音声
- 音量
- 優先度
- 競合時動作

スケジュールタイプ：

- 一回
- 毎日
- 平日
- 曜日指定
- 指定日
- Cron形式（Advanced）

例：

```text
Name
Lunch Bell

Schedule
Daily

Time
12:00:00

Audio
lunch.wav

Volume
80%

Conflict policy
Queue
```

---

# 9. 再生競合制御

以下をサポートする。

### Queue

現在再生中の音声終了後に再生。

### Interrupt

現在の音声を停止して再生。

### Skip

他の音声が再生中ならスキップ。

内部的には再生キューを一本化する。

---

# 10. Priority

整数値によるPriorityを内部的に持つ。

標準：

```text
Emergency      100
High            50
Normal          10
Background       0
```

通常UIでは、

- Emergency
- High
- Normal
- Low

として表示してよい。

---

# 11. Audio Library

対応フォーマット：

- WAV
- MP3
- FLAC
- OGG
- M4A

アップロード後、内部フォーマットへ正規化する。

推奨：

```text
WAV
48kHz
16-bit PCM
Stereo
```

オリジナルファイルも保存する。

構造：

```text
data/audio/

<uuid>/
  original.mp3
  playback.wav
  metadata.json
```

---

# 12. Audio Device Manager

使用可能な出力デバイスを自動列挙する。

例：

```text
Built-in Audio Analog Stereo
HDMI 0
HDMI 1
USB Audio DAC
```

WebUIから選択可能とする。

保存する際は、

```text
hw:2,0
```

のような単純なカード番号だけに依存しない。

USB抜き差しで番号が変わるため、

- PipeWire node name
- ALSA card ID
- USB VID/PID
- device description

等から永続的な識別子を生成する。

---

# 13. Audio Test

Devicesページに、

```text
Test Audio
```

ボタンを設ける。

テスト用短音声を対象デバイスから再生する。

---

# 14. Audio Agent

実際の音声出力はホスト側systemdサービスとして動作させる。

理由：

Dockerコンテナへ音声デバイスを直接渡すより、

- USB DAC抜き差し
- HDMI
- PipeWire
- ALSA
- 権限
- デバイス変更

への対応が容易になるため。

Audio Agentはlocalhostのみlistenする。

例：

```text
127.0.0.1:8031
```

API：

```text
GET /devices

POST /play
POST /stop
POST /test
POST /volume
```

外部ネットワークには公開しない。

---

# 15. Audio Agentの再生方式

音声ファイルを再生時刻になってからプロセス起動する方式だけには依存しない。

可能であれば、

```text
load audio
↓
open output
↓
wait until target monotonic time
↓
start playback
```

とする。

これにより再生時刻のばらつきを減らす。

MVPではffmpeg / pw-play等を利用してもよい。

後から常駐型再生エンジンへ移行可能な構造にする。

---

# 16. Application Time Provider

スケジューラはOS時刻を直接使用しない。

独自のTime Providerを実装する。

概念：

```text
NTP Time
      │
      ▼
NTP Synchronizer
      │
      ▼
base_ntp_time
base_monotonic
      │
      ▼
Application Time
```

現在時刻：

```text
application_time =
    base_ntp_time
    +
    (CLOCK_MONOTONIC - base_monotonic)
```

とする。

これによりOS時計補正による急激な時刻ジャンプの影響を避ける。

---

# 17. NTP

初期設定：

```text
ntp.nict.jp
time.cloudflare.com
time.google.com
```

複数NTPサーバーを設定可能にする。

設定項目：

- Primary NTP
- Secondary NTP
- Tertiary NTP
- Sync Interval
- Timeout

標準同期間隔：

```text
300秒
```

---

# 18. NTP障害時

NTP取得失敗時でもSchedulerを停止させない。

最後に正常取得した、

```text
base_ntp_time
base_monotonic
```

から時刻を継続する。

状態：

```text
Synchronized
Degraded
Unsynchronized
```

を持つ。

例：

```text
Synchronized
last sync 2 minutes ago

Degraded
last sync 8 hours ago
```

---

# 19. Scheduler

Schedulerは100～250ms程度の周期で次のイベントを確認する。

イベント発火済み記録を持ち、同じイベントを二重再生しない。

最低でも、

```text
schedule_id
scheduled_at
executed_at
result
```

を保存する。

---

# 20. VOICEVOX

VOICEVOX ENGINEをDockerで実行する。

BackendからHTTP APIでアクセスする。

FrontendからVOICEVOX ENGINEへ直接アクセスさせない。

---

# 21. VOICEVOX Template

テンプレート例：

```text
{{ event_name }}まであと {{ days_until(event_date) }} 日です
```

変数：

```text
event_name = NHKロボコン
event_date = 2026-09-15
```

展開結果：

```text
NHKロボコンまであと18日です
```

---

# 22. Template Syntax

Jinja風だが、セキュリティ上Jinja2をそのまま無制限実行しない。

許可されたマクロのみ評価する専用Template Engineを実装する。

サポート例：

```text
{{ today() }}

{{ today("YYYY/MM/DD") }}

{{ now("HH:mm") }}

{{ year() }}

{{ month() }}

{{ day() }}

{{ weekday() }}

{{ days_until("2026-09-15") }}

{{ days_since("2026-04-01") }}

{{ event_name }}

{{ days_until(event_date) }}
```

---

# 23. Variables

ユーザー定義変数をサポートする。

型：

- String
- Integer
- Float
- Date
- DateTime
- Boolean

例：

```text
event_name
String
NHKロボコン

event_date
Date
2026-09-15
```

---

# 24. VOICEVOX Template設定

テンプレートごとに、

- Speaker
- Style
- Speed
- Pitch
- Intonation
- Volume
- Pre/Post silence

を保存する。

---

# 25. VOICEVOX Preview

テンプレート編集画面に、

```text
Preview Text

Generate Preview

Play Preview
```

を設ける。

Preview Textでは現在時刻・変数を使用して展開結果を確認できる。

---

# 26. VOICEVOX Prefetch

VOICEVOX音声は原則、予定再生時刻より前に生成する。

標準：

```text
prefetch = 10 minutes
```

例：

```text
Playback
12:00

VOICE generation
11:50
```

---

# 27. Prefetch Scheduler

通常Schedulerとは別にVoice Prefetch Schedulerを設ける。

処理：

```text
Upcoming Schedule
      ↓
VOICEVOX template?
      ↓
Template evaluation
      ↓
Cache lookup
      ↓
Cache miss
      ↓
VOICEVOX generation
      ↓
WAV cache
```

---

# 28. Voice Cache

キャッシュキーは最低でも、

```text
speaker
style
speed
pitch
intonation
volume
expanded_text
VOICEVOX version
```

を含めたSHA-256とする。

例：

```text
SHA256(
  speaker +
  style +
  parameters +
  expanded_text
)
```

保存先：

```text
data/voice-cache/<sha256>.wav
```

---

# 29. Prefetch Failure

VOICEVOX生成失敗時は一定間隔で再試行。

例：

```text
10分前
5分前
2分前
30秒前
```

ただし無限リトライしない。

再生時刻になってもキャッシュが存在しない場合、

設定により、

```text
Skip
Fallback audio
Play previous cache
```

を選択可能にする。

初期版は、

```text
Skip + Error Log
```

でよい。

---

# 30. Dynamic Templateの扱い

以下のようなテンプレート：

```text
現在時刻は {{ now("HH:mm") }} です
```

は早すぎるPrefetchでは内容がずれる。

そのためテンプレートに、

```text
Generation Strategy
```

を設ける。

初期対応：

```text
Before Playback
```

+ lead time。

将来的に、

```text
Daily
When Variable Changes
Fixed Time
```

にも対応可能とする。

---

# 31. Database

主要テーブル：

```text
settings

audio_files

schedules

schedule_rules

voice_templates

voice_variables

voice_cache

playback_queue

playback_history

ntp_history

system_events
```

---

# 32. Playback History

記録：

```text
id
schedule_id

scheduled_at
started_at
finished_at

delay_ms

audio_device

result

error_message
```

例えば：

```text
Scheduled   12:00:00.000
Started     12:00:00.036
Delay       +36 ms
Result      Success
```

---

# 33. Logs画面

WebUIから以下を確認できるようにする。

- Playback
- Scheduler
- VOICEVOX
- NTP
- System

ログレベル：

```text
DEBUG
INFO
WARNING
ERROR
```

---

# 34. WebSocket

WebUIの状態表示にはWebSocketを利用する。

対象：

- 現在時刻
- 次回再生
- 再生状態
- VOICEVOX生成状態
- NTP状態
- Audio device
- システム状態

---

# 35. API

基本：

```text
/api/v1/
```

## Schedule

```text
GET    /schedules
POST   /schedules
GET    /schedules/{id}
PUT    /schedules/{id}
DELETE /schedules/{id}

POST /schedules/{id}/enable
POST /schedules/{id}/disable
POST /schedules/{id}/run
```

## Audio

```text
GET    /audio
POST   /audio
DELETE /audio/{id}

POST /audio/{id}/play
```

## Devices

```text
GET /devices
POST /devices/test

GET /devices/current
PUT /devices/current
```

## VOICEVOX

```text
GET /voicevox/status
GET /voicevox/speakers

GET    /voice/templates
POST   /voice/templates
GET    /voice/templates/{id}
PUT    /voice/templates/{id}
DELETE /voice/templates/{id}

POST /voice/templates/{id}/preview
POST /voice/templates/{id}/generate
```

## Variables

```text
GET    /variables
POST   /variables
PUT    /variables/{id}
DELETE /variables/{id}
```

## Time

```text
GET /time
GET /time/status
POST /time/sync
```

---

# 36. Authentication

MVPではLAN内利用を想定する。

ただしBackend側ではAuthenticationを後付けしやすい構造にする。

Phase 2として、

- Local username/password
- Session cookie
- CSRF protection

を追加可能にする。

外部公開する場合は認証を必須とする。

---

# 37. Install Script

リポジトリ直下に、

```text
install.sh
```

を必ず実装する。

実行方法：

```bash
curl等で取得
cd raspi-audio-scheduler
sudo ./install.sh
```

または、

```bash
git clone ...
cd raspi-audio-scheduler
sudo ./install.sh
```

とする。

---

# 38. install.sh 要件

インストーラーは以下を自動実行する。

### OS確認

```text
architecture = aarch64
```

を確認。

Raspberry Pi 4かどうかを可能な範囲で確認する。

非対応環境の場合は警告を表示する。

---

### パッケージ更新

```bash
apt update
```

必要に応じ、

```bash
apt upgrade
```

はユーザーに選択させる。

自動でdistribution upgradeはしない。

---

### 必須パッケージ

最低限：

```text
curl
git
jq
ffmpeg
pipewire
pipewire-pulse
wireplumber
alsa-utils
python3
python3-venv
ca-certificates
```

---

### Docker

Dockerが存在しない場合のみインストール。

既存Docker環境を破壊しない。

Docker Compose pluginも確認する。

---

### ユーザー

専用ユーザー：

```text
audio-scheduler
```

を作成する。

ログイン不可：

```text
/usr/sbin/nologin
```

を基本とする。

必要な、

```text
audio
video
```

等のgroupへ追加する。

---

# 39. ディレクトリ

標準配置：

```text
/opt/raspi-audio-scheduler
```

データ：

```text
/var/lib/raspi-audio-scheduler
```

設定：

```text
/etc/raspi-audio-scheduler
```

ログ：

```text
/var/log/raspi-audio-scheduler
```

---

# 40. 権限

例：

```text
/opt/raspi-audio-scheduler
root:root

/var/lib/raspi-audio-scheduler
audio-scheduler:audio-scheduler

/etc/raspi-audio-scheduler
root:audio-scheduler
```

---

# 41. Environment File

インストール時に、

```text
/etc/raspi-audio-scheduler/app.env
```

を作成する。

例：

```text
APP_PORT=8080

DATA_DIR=/var/lib/raspi-audio-scheduler

NTP_PRIMARY=ntp.nict.jp
NTP_SECONDARY=time.cloudflare.com
NTP_INTERVAL=300

VOICEVOX_URL=http://127.0.0.1:50021

VOICE_PREFETCH_SECONDS=600
```

---

# 42. VOICEVOX Installation

Docker ComposeからARM64対応VOICEVOX ENGINE CPU版を起動する。

install.shで、

```text
docker compose pull
```

を実行。

起動後、

```text
/version
```

等を利用してhealth checkを行う。

VOICEVOXの起動に失敗してもシステム全体を利用不能にせず、

```text
VOICEVOX Unavailable
```

状態とする。

---

# 43. Audio Configuration

PipeWire利用を前提とする。

install.shは、

```text
wpctl
pw-cli
```

等が利用可能か確認する。

利用可能なAudio deviceを列挙する。

例：

```text
Detected audio outputs:

1. Built-in Analog
2. HDMI
3. USB DAC
```

ただしインストール時に出力先を固定する必要はない。

WebUIから後で設定可能とする。

---

# 44. systemd

以下を作成する。

```text
raspi-audio-agent.service
raspi-audio-scheduler.service
```

必要に応じて、

```text
raspi-audio-scheduler.target
```

を用意してまとめて管理する。

---

# 45. systemd dependencies

Backend：

```text
After=network-online.target docker.service
Wants=network-online.target
```

Audio Agent：

```text
After=pipewire.service
```

環境に応じてユーザーPipeWire sessionとの関係を考慮する。

Headless環境でも安定動作する方法を採用すること。

---

# 46. Firewall

install.shで勝手にFirewall設定を変更しない。

標準ポート：

```text
8080/tcp
```

READMEに必要なFirewallルールを記載する。

---

# 47. Installer最後

最後に以下を表示する。

```text
Raspberry Pi Audio Scheduler installed successfully.

Web UI:
http://192.168.1.10:8080

Services:
audio-agent    running
backend        running
voicevox       running

NTP:
synchronized

Audio:
3 outputs detected
```

IPアドレスを自動検出する。

---

# 48. install.sh 冪等性

重要：

install.shは複数回実行してもシステムを破壊しないようにする。

つまり、

```text
package installed?
user exists?
directory exists?
Docker installed?
service exists?
```

を確認してから処理する。

---

# 49. update.sh

インストールスクリプトだけでなく、

```text
update.sh
```

も作成する。

処理：

```text
現在設定をバックアップ

git pull / release取得

Docker image pull

DB migration

frontend/backend更新

systemd restart

health check
```

失敗時は可能な限りロールバック可能にする。

---

# 50. uninstall.sh

以下の選択肢を設ける。

```text
Remove application only
```

または、

```text
Remove application and all data
```

デフォルトではデータを削除しない。

---

# 51. Backup

DBバックアップ機能を用意する。

標準：

```text
/var/lib/raspi-audio-scheduler/backups
```

SQLite DBを定期バックアップ。

例えば、

```text
1日1回
7世代
```

---

# 52. Health Check

Backend：

```text
GET /api/v1/system/health
```

レスポンス例：

```json
{
  "status": "ok",
  "scheduler": true,
  "ntp": true,
  "audio_agent": true,
  "voicevox": true
}
```

---

# 53. 開発環境

ローカルPCでも開発できるようにする。

```text
.devcontainer/
```

を用意してDev Container対応する。

開発時：

```text
Frontend
Backend
SQLite
VOICEVOX
```

をPC上で動作可能にする。

Audio Agentについては、

```text
mock audio backend
```

を用意する。

これによりRaspberry Piなしでも開発可能にする。

---

# 54. Mock Audio Device

開発環境では、

```text
Mock Analog
Mock HDMI
Mock USB DAC
```

を返せるようにする。

Play要求時には実際には再生せず、

```text
PLAY /audio/test.wav
```

をログ出力する。

---

# 55. Testing

## Unit Test

- Scheduler
- Date calculation
- Macro parsing
- NTP offset
- Voice cache
- Schedule rule
- Variable expansion

## Integration Test

- Backend ↔ SQLite
- Backend ↔ VOICEVOX
- Backend ↔ Audio Agent

## Pi Hardware Test

- 3.5mm
- HDMI
- USB DAC
- USB DAC hotplug
- NTP disconnect
- Network disconnect
- reboot
- power loss recovery

---

# 56. 特に重要なテスト

### 二重再生防止

OS時計が前後した場合でも同一Scheduleを二度再生しない。

### 再起動

予定時刻直前に再起動した場合。

### NTP障害

NTPサーバーにアクセスできなくなった場合。

### VOICEVOX障害

VOICEVOX ENGINEが停止している場合。

### USB DAC抜去

再生直前または再生中にDACが抜かれた場合。

---

# 57. 開発フェーズ

## Phase 1 — 基盤

実装：

- FastAPI
- React
- SQLite
- Docker Compose
- basic UI
- Settings API
- Health check

---

## Phase 2 — Audio

実装：

- Audio Agent
- PipeWire device detection
- Device selection
- WAV playback
- Upload
- ffmpeg normalization
- Test playback

完成条件：

WebUIからファイルをアップロードし、任意デバイスから再生できる。

---

## Phase 3 — NTP Clock

実装：

- NTP client
- monotonic clock
- offset
- fallback
- WebUI status

完成条件：

SchedulerがOS clockではなくApplication Timeを利用する。

---

## Phase 4 — Scheduler

実装：

- Daily
- Date
- Weekday
- Weekdays
- Queue
- Interrupt
- Skip
- Playback history

完成条件：

WebUIから登録した予定時刻に音声を再生できる。

---

## Phase 5 — VOICEVOX

実装：

- VOICEVOX ENGINE
- Speaker取得
- Voice generation
- Preview
- Cache

完成条件：

WebUIで文章を入力して音声生成・再生できる。

---

## Phase 6 — Template Macro

実装：

- Variables
- Template parser
- today
- now
- days_until
- days_since
- Date formatting

完成条件：

```text
イベントまであと
{{ days_until(event_date) }}
日です
```

を正常に音声化できる。

---

## Phase 7 — Prefetch

実装：

- Prefetch Scheduler
- Cache key
- generation queue
- retry
- failure handling

完成条件：

VOICEVOXを再生時刻より前に生成しておき、予定時刻にはキャッシュ済みWAVのみを再生する。

---

## Phase 8 — Installer

実装：

```text
install.sh
update.sh
uninstall.sh
```

systemd、Docker、PipeWire、データディレクトリ等を含めた自動構築を行う。

---

## Phase 9 — UI仕上げ

Cloudflare風デザイン。

画面：

```text
Overview
Schedules
Audio
VOICEVOX
Variables
Devices
Time
Logs
Settings
```

Responsive対応。

---

# 58. MVP完成条件

以下をすべて満たした段階をv1.0とする。

1. WebUIへアクセスできる。

2. 音声ファイルをアップロードできる。

3. 3.5mm / HDMI / USB DACを選択できる。

4. WebUIからテスト再生できる。

5. 毎日・曜日・指定日のScheduleを登録できる。

6. 指定時刻に音声を再生できる。

7. アプリ独自にNTP時刻を取得する。

8. OS clockの変更で二重再生しない。

9. VOICEVOXで音声生成できる。

10. VOICEVOX Templateを作成できる。

11. Macroを利用できる。

12. VOICEVOX音声を事前生成できる。

13. 音声キャッシュを利用できる。

14. Playback historyを確認できる。

15. Raspberry Pi再起動後、自動復帰する。

16. `install.sh`のみで新しいRaspberry Piへ導入できる。

---

# 59. 実装時の優先原則

特に以下を守る。

### 時刻精度

スケジューラからOS wall clockへの直接依存を避ける。

### 再生処理の単純化

予定時刻に複雑な処理を行わない。

再生時刻には原則、

```text
cache済みWAV
        ↓
Audio Agent
        ↓
Playback
```

のみとする。

### VOICEVOX事前生成

音声生成速度を再生時刻の正確性に影響させない。

### Audio Device抽象化

ALSA番号を直接DBへ保存しない。

### 冪等インストーラー

`install.sh`を再実行可能にする。

### 障害分離

VOICEVOXが落ちても通常音声再生を継続する。

NTPが落ちても最後の同期時刻から動作継続する。

WebUIが落ちてもAudio Agentが不必要に停止しない。

---

# 60. 将来拡張

v1.0以降の候補。

- 複数Raspberry Pi同期再生
- MQTT
- REST API外部制御
- Discord連携
- GPIO入力による再生
- 緊急放送
- Webhook
- プレイリスト
- BGM
- 音声フェード
- 音声ミキシング
- Bluetooth Audio
- 複数Audio Zone
- Calendar連携
- CSV Schedule import/export
- 設定Backup/Restore
- HTTPS
- User Authentication
- PWA

---

# 61. 最初に実装する順番

実装担当は以下の順番で進めること。

```text
1. Repository構築

2. Dev Container

3. Backend / Frontend skeleton

4. SQLite / migration

5. Audio Agent

6. Audio device detection

7. Audio upload / playback

8. NTP Time Provider

9. Scheduler

10. Playback history

11. VOICEVOX ENGINE

12. VOICEVOX generation

13. Template Engine

14. Prefetch Scheduler

15. Voice Cache

16. Cloudflare-style UI

17. install.sh

18. update.sh

19. uninstall.sh

20. Raspberry Pi 4実機試験
```

初期段階からinstall.shを完全に仕上げようとはせず、各機能が安定した段階でInstallerへ順次組み込む。

ただしv1.0完成条件として、クリーンインストールしたRaspberry Pi OS Lite 64-bit環境に対し、

```bash
sudo ./install.sh
```

を実行するだけで、VOICEVOXを含むシステム一式が利用可能になることを必須条件とする。