# BME280 ロガー

## Overview
BME280 から取得したデータを InfluxDB (v2系) に格納するスクリプト。

InfluxDB に格納したレコードを Grafana で表示するためのダッシュボード (JSON) サンプル付き。

## Prerequirements
ハードウェアとして、以下が必要。

- 環境センサーモジュール BME280 (I2C インタフェース)
- Raspberry Pi や USB-I2C 変換モジュール (FTDI 社 FT232H 等) などの BME280 をコントロールするためのハードウェア

結果格納とダッシュボード表示のために以下が必要。

- InfluxDB OSS 2
- Grafana

また、本スクリプトを実行するために、以下が必要。

- Python 3
- uv

## Setup

### 実行環境

クローン後、init.sh を実行し、必要な Python モジュールをダウンロード。
```
cd /opt
git clone https://github.com/gcch/bme280-logger.git
cd bme280-logger
./init.sh
```

設定ファイル `config.ini` を作成。InfluxDB のアクセス情報 `url` `org` `token` `bucket` を設定。
```
cp config.ini.sample config.ini
vi config.ini
```

定期実行のため、cron の設定を実施。
```
echo "*/10 * * * * root /opt/bme280-logger/run.sh" > /etc/cron.d/bme280-logger
```

### （必要に応じて）Proxmox VE ホストでのデバイスアクセス許可設定

ロガーを LXC 環境で動作させる場合、LXC への USB デバイスのアクセス許可が必要。
`/etc/pve/lxc/<CTID>.conf` に以下を追記。
```
lxc.cgroup2.devices.allow: c 189:* rwm
lxc.mount.entry: /dev/bus/usb/001 dev/bus/usb/001 none bind,optional,create=dir
```

### （必要に応じて）FTDI社デバイス（FT232Hなど）経由でアクセスさせる場合
ドライバ `ftdi_sio` で読み込まれてしまうと、I2C でアクセスできなくなってしまうため、以下内容の `/etc/modprobe.d/blacklist-ftdi.conf` を作成。
```
blacklist ftdi_sio
```

デバイスを抜き差しし、`lsusb` コマンドで `Driver` が `[none]` 表示になることを確認。

```
# lsusb
   :
Bus 001 Device 013: ID 0403:6014 Future Technology Devices International, Ltd FT232H Single HS USB-UART/FIFO IC
   :
# lsusb -t
/:  Bus 001.Port 001: ...
    |__ Port 003: Dev 013, If 0, Class=Vendor Specific Class, Driver=[none], 480M
   :
```
