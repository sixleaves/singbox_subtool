# singbox_subtool
- 改造了Toperlock的开源项目https://github.com/Toperlock/sing-box-subscribe.git
- 用面向对象重构。
- 去除后端功能.方便程序员自行实用。

## 使用步骤
- 1.创建如下的providers.json文件。url部分填入订阅地址
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
            "user_agent":"v2rayng"
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