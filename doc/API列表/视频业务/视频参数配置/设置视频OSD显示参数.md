# 设置视频OSD显示参数

> 接口说明
> 本接口用于设置视频OSD显示参数。仅支持海康SDK、ehome两种协议的监控点，且级联点位不支持该功能。
> 进行设置视频OSD显示参数操作的用户需要配置相应监控点的OSD叠加权限，本接口会根据传入的userId进行权限过滤。
> 注意：参数设置是否生效与设备支持情况有关，不同型号设备支持情况不同。本接口设置的Y坐标值和下发到设备中的值可能存在不一致的情况，设备端OSD的Y坐标是有限制的，SDK协议下发是4字节对齐的，下发的值会进行转换成16的倍数。原因为：防止P制和N制切换时OSDY坐标的的较大偏移；OSD的最小字体就是16*16，如果Y坐标不做限制的话就会相互叠加在一块。

## 基本信息
|项目|值|
|---|---|
|接口版本|v1|
|适配版本|综合安防管理平台iSecure Center V1.4及以上版本|
|接口地址|`/api/video/v1/picParams/udpate`|
|请求方法|`POST`|
|数据提交方式|application/json|

## 快速调用
```text
POST /api/video/v1/picParams/udpate
```

## 请求参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`cameraIndexCode`|`body`|`string`|是|监控点唯一标识,从分页获取监控点资源接口获取返回参数cameraIndexCode|
|`channelName`|`body`|`string`|是|通道名称|
|`isShowChanName`|`body`|`integer`|是|是否显示通道名称，0-不显示；1-显示|
|`channelNameXPos`|`body`|`integer`|是|通道名称显示X坐标|
|`channelNameYPos`|`body`|`integer`|是|通道名称显示Y坐标|
|`hourOSDType`|`body`|`integer`|是|小时制，0代表24小时制；1代表12小时制或am/pm|
|`isShowOSD`|`body`|`integer`|是|是否显示OSD，0-不显示；1-显示|
|`osdXPos`|`body`|`integer`|是|OSD显示X坐标|
|`osdYPos`|`body`|`integer`|是|OSD显示Y坐标|
|`osdType`|`body`|`integer`|是|OSD显示类型值，参考附录A.74 OSD显示类型及说明|
|`osdAttrib`|`body`|`integer`|是|OSD属性，1-透明,闪烁；2-透明,不闪烁；3-闪烁,不透明；4-不透明,不闪烁|
|`isShowWeek`|`body`|`integer`|是|是否显示星期，0-不显示；1-显示|

## 请求参数示例
```json
{
  "cameraIndexCode": "fee3d641f0e44ecCC9b9def2b423b7eb",
  "channelName": "camera 01",
  "isShowChanName": 1,
  "channelNameXPos": 16,
  "channelNameYPos": 16,
  "hourOSDType": 0,
  "isShowOSD": 1,
  "osdXPos": 16,
  "osdYPos": 16,
  "osdType": 1,
  "osdAttrib": 1,
  "isShowWeek": 1
}
```

## 返回参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`code`|`body`|`string`|否|返回码，0 – 成功，其他- 失败，参考附录E.1.1 视频应用错误码|
|`msg`|`body`|`string`|否|返回描述|
|`data`|`body`|`string`|否|返回数据|

## 返回参数示例
```json
{
  "code": "0",
  "msg": "success",
  "data": null
}
```
