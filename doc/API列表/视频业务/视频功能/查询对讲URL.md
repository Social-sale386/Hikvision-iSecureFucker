# 查询对讲URL

> 接口说明
> 该接口用于获取监控点的对讲url，为保证数据的安全性，取流URL设有有效时间，有效时间为5分钟。

## 基本信息
|项目|值|
|---|---|
|接口版本|v1|
|适配版本|综合安防管理平台iSecure Center V1.2及以上版本|
|接口地址|`/api/video/v1/cameras/talkURLs`|
|请求方法|`POST`|
|数据提交方式|application/json|

## 快速调用
```text
POST /api/video/v1/cameras/talkURLs
```

## 请求参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`cameraIndexCode`|`body`|`string`|是|监控点唯一标识，分页获取监控点资源接口获取返回参数cameraIndexCode|
|`transmode`|`body`|`integer`|否|协议类型,|
|`protocol`|`body`|`string`|否|取流协议（应用层协议），“rtsp”:RTSP协议；“ws”:WS协议；“wss”:WSS协议，WS和WSS协议仅供开放平台开发播放控件使用，不直接开放给第三方使用，且使用WS和WSS协议取流要求mgc版本不能低于V5.13.100。参数不填，默认为RTSP协议。（此参数vms不做范围校验，由vnsc进行校验，以便于协议拓展）|
|`expand`|`body`|`string`|否|扩展内容，格式：key=value， 调用方根据其播放控件支持的解码格式选择相应的封装类型； 支持的内容详见附录F expand扩展内容说明|
|`eurlExpand`|`body`|`string`|否|url扩展字段,生成取流短连接扩展字段，按照取流客户端对url特殊字段校验，可添加该字段至生成的短连接末尾|

补充说明:
- 0: UDP
- 1: TCP
- 未填默认为TCP

## 请求参数示例
```json
{
  "cameraIndexCode": "fee3d641f0e44ecCC9b9def2b423b7eb",
  "transmode": 1,
  "expand": "streamform=ps",
  "eurlExpand": "url扩展字段"
}
```

## 返回参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`code`|`body`|`string`|否|返回码，0 – 成功，其他- 失败，参考附录E.1.1 视频应用错误码|
|`msg`|`body`|`string`|否|返回描述|
|`data`|`body`|`object`|否|返回数据|
|`+url`|`body`|`string`|否|取流URL|

## 返回参数示例
```json
{
  "code": "0",
  "msg": "success",
  "data": {
    "url": "rtsp://10.2.145.66:655/openUrl/CLJ52BW"
  }
}
```
