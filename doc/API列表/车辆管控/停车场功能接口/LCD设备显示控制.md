# LCD设备显示控制

> 接口说明
> 简述：直接控制LED设备显示内容。
> 支持：通过车道、设备编号对LCD进行内容设置，如果传入车道，将对车道下所有的LCD设备发送控屏命令。

## 基本信息
|项目|值|
|---|---|
|接口版本|v1|
|适配版本|综合安防管理平台iSecure Center V2.1.0及以上版本|
|接口地址|`/api/pms/v1/device/lcdControl`|
|请求方法|`POST`|
|数据提交方式|application/json|

## 快速调用
```text
POST /api/pms/v1/device/lcdControl
```

## 请求参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`roadwaySyscode`|`body`|`string`|是|车道编号,查询出入口设备关联关系接口获取返回参数roadwaySyscode|
|`deviceSyscode`|`body`|`string`|否|设备编号,查询出入口设备关联关系接口获取返回参数deviceSyscode,（为空的话车道下所有lcd设备显示；不为空的话指定lcd设备显示）|
|`lcdTitle`|`body`|`object[]`|否|控屏标题内容，守蔚设备最多两行|
|`+line`|`Body`|`number`|否|标题行号|
|`+secText`|`Body`|`string`|否|标题内容|
|`lcdContent`|`body`|`object[]`|否|控屏内容配置，守蔚设备最多四行|
|`+line`|`Body`|`number`|否|内容行号|
|`+secText`|`Body`|`string`|否|显示内容|

## 请求参数示例
```json
{
  "roadwaySyscode": "279434554ac04f58a5241e1425ee91ab",
  "deviceSyscode": "1861b3fae0a844b681e8980224b58f7c",
  "lcdTitle": [
    {
      "line": 1,
      "secText": "第1行标题"
    },
    {
      "line": 2,
      "secText": "第2行标题"
    }
  ],
  "lcdContent": [
    {
      "line": 1,
      "secText": "第1行内容"
    },
    {
      "line": 2,
      "secText": "第2行内容"
    },
    {
      "line": 3,
      "secText": "第3行内容555"
    },
    {
      "line": 4,
      "secText": "第4行内容666"
    }
  ]
}
```

## 返回参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`code`|`body`|`string`|是|请求结果码|
|`msg`|`body`|`string`|是|提示信息|

## 返回参数示例
```json
{
  "code": "0",
  "msg": "success"
}
```
