# BME280 ロガー

## Overview
BME280 から取得したデータを InfluxDB (v2系) に格納するスクリプト。

InfluxDB に格納したレコードを Grafana で表示するためのダッシュボード (JSON) サンプル付き。

## Prerequirements
ハードウェアとして、以下が必要。

- 環境センサーモジュール BME280
- Raspberry Pi 等の BME280 をコントロールするためのハードウェア

結果格納とダッシュボード表示のために以下が必要。

- InfluxDB OSS 2
- Grafana

また、本スクリプトを実行するために、以下が必要。

- Python 3
- uv

## Setup

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
echo "* 0 * * * root /opt/bme280-logger/run.sh" > /etc/cron.d/bme280-logger
```


