# LED设备控屏

> 接口说明
> 简述：直接控制LED设备显示内容。
> 支持：通过车道、设备编号对LED进行内容设置。

## 基本信息
|项目|值|
|---|---|
|接口版本|v1|
|适配版本|综合安防管理平台iSecure Center V1.5及以上版本|
|接口地址|`/api/pms/v1/device/led/control`|
|请求方法|`POST`|
|数据提交方式|application/json|

## 快速调用
```text
POST /api/pms/v1/device/led/control
```

## 请求参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`deviceSyscode`|`body`|`string`|否|设备编号,查询出入口设备关联关系接口获取返回参数deviceSyscode,（车道编号和设备编号必填其一）|
|`roadwaySyscode`|`body`|`string`|否|车道编号,查询出入口设备关联关系接口获取返回参数roadwaySyscode,（车道编号和设备编号必填其一）|
|`ledContent`|`body`|`object`|否|控屏内容|
|`+line`|`Body`|`number`|否|行号|
|`+fontConfig`|`Body`|`string`|否|行内字体样式，三个参数依次参考对齐方式，显示方式, 字体颜色，附录A.86 文字对齐方式，附录A.87 文字显示方式，详见附录A.85 文字颜色|
|`+showConfig`|`Body`|`string`|否|显示内容配置|

## 请求参数示例
```json
{
  "deviceSyscode": "agfdgdfgdfgdfg3424232342343",
  "roadwaySyscode": "afc72099c93u239487234892",
  "ledContent": {
    "line": 1,
    "fontConfig": "[1,1,1]",
    "showConfig": "欢迎光临"
  }
}
```

## 返回参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`code`|`body`|`string`|否|返回码，0 – 成功，其他- 失败，参考附录E.3.1 停车场应用错误码|
|`msg`|`body`|`string`|否|返回描述|
|`data`|`body`|`string`|否|为空|

## 返回参数示例
```json
{
  "code": "0",
  "msg": "Success",
  "data": null
}
```
