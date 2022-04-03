# comist

## スクレイピング手順

### Windows

1. mongoDBを起動する  
   `mongod --dbpath D:\path\to\db_data\dir --logpath D:\hoge\mongodb.log`
2. rootディレクトリでクロールを実施

### Linux

1. mongo DBを起動する
   `systemctl start mongod.service`
   (停止時は`systemctl stop mongod.service`)
2. rootディレクトリでクロールを実施
   `scrapy crawl GetComics -a category=xxx`

categoryはカンマ区切りで複数指定可
category一覧↓

- eromanga-night
- gyaru
- hinnyu
- jingai-kemono
- jk-jc
- jyukujyo-hitozuma
- kinshinsoukan
- kosupure
- kyonyu-binyu
- netorare-netori
- ol-sister
- onesyota
- rape
- rezu-yuri



3. Comicsディレクトリに自動でカテゴリ別のディレクトリが作成され、保存される


