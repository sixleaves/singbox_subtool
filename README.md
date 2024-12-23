# singbox_subtool
- 改造了Toperlock的开源项目https://github.com/Toperlock/sing-box-subscribe.git
- 用面向对象重构。
- 去除后端功能.方便程序员自行实用。
- 支持最新版本的singbox订阅，不支持旧版本。

## 使用步骤
- 1.创建如下的providers.json文件。url部分填入订阅地址
  - url:订阅的地址
  - tag:给这个订阅地址一个名字
  - prefix:给每个节点名字添加的前缀
  - insecure:是否开启证书tls证书校验。如果不开启会被中间人攻击，导致数据泄漏。
```json
{
    "subscribes":[
        {
            "url": "",
            "tag": "kfc",
            "enabled": true,
            "emoji": 0,
            "subgroup": "",
            "prefix": "",
            "user_agent":"v2rayng",
            "insecure": true
        }
    ],
    "auto_set_outbounds_dns":{
        "proxy": "",
        "direct": ""
    },
    "save_config_path": "./config.json",
    "auto_backup": false,
    "exclude_protocol":"ssr",
    "config_template": "",
    "Only-nodes": false
}
```
- 2.直接运行main.py就会在save_config_path配置的目录下生成配置文件.