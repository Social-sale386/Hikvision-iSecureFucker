# 获取监控点回放取流URLv2

> 接口说明
> 1.平台正常运行；平台已经添加过设备和监控点信息。
> 2.平台需要安装mgc取流服务。
> 3.三方通过openAPI获取到监控点数据，依据自身业务开发监控点导航界面。
> 4.调用本接口获取回放取流URL，协议类型包括：hik、rtsp、rtmp、hls（只支持云存储）、ws。
> 5.通过开放平台的开发包进行录像回放或者使用标准的GUI播放工具进行录像回放。（开发包使用说明参考开发包的使用说明文档）
> 6.为保证数据的安全性，取流URL设有有效时间，有效时间为5分钟。

## 基本信息
|项目|值|
|---|---|
|接口版本|v2|
|适配版本|综合安防管理平台iSecure Center V1.4及以上版本|
|接口地址|`/api/video/v2/cameras/playbackURLs`|
|请求方法|`POST`|
|数据提交方式|application/json|

## 快速调用
```text
POST /api/video/v2/cameras/playbackURLs
```

## 请求参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`cameraIndexCode`|`body`|`string`|是|监控点唯一标识，分页获取监控点资源接口获取返回参数cameraIndexCode|
|`recordLocation`|`body`|`string`|否|存储类型,0：中心存储|
|`protocol`|`body`|`string`|否|取流协议（应用层协议）。 “hik”:HIK私有协议，使用视频SDK进行播放时，传入此类型；“rtsp”:RTSP协议；“rtmp”:RTMP协议；“hls”:HLS协议；“hlss”:基于ssl/tls的HLS协议；“ws”:Websocket协议；“wss”:基于ssl/tls的Websockets协议；“httpflv”:HTTP-FLV协议；“httpsflv”:基于ssl/tls的HTTP-FLV协议；“httpmp4”:HTTP-MP4协议；“httpsmp4”:基于ssl/tls的HTTP-MP4协议。 参数不填，默认为HIK协议，最大长度：64。 注： 1、HLS协议只支持海康SDK协议、EHOME协议、ONVIF协议接入的设备；只支持H264、H265视频编码和AAC音频编码；云存储版本要求v2.2.4及以上的2.x版本，或v3.0.5及以上的3.x版本；需在运管中心-视频联网共享中切换成启动平台外置VOD； 2、Websocket协议仅限使用H5视频播放器取流播放； 3、HTTP-FLV协议只支持海康SDK协议、EHOME协议、ONVIF协议接入的设备；只支持H264视频编码和AAC音频编码；需在运管中心-视频联网共享中切换成启动平台外置VOD； 4、HTTP-MP4协议仅限录像下载使用。|
|`transmode`|`body`|`integer`|否|传输协议（传输层协议）0:UDP|
|`beginTime`|`body`|`string`|是|开始查询时间（IOS8601格式：yyyy-MM-dd’T’HH:mm:ss.SSSXXX）|
|`endTime`|`body`|`string`|是|结束查询时间，开始时间和结束时间相差不超过三天；|
|`uuid`|`body`|`string`|否|分页查询id,上一次查询返回的uuid，用于继续查询剩余片段，默认为空字符串。当存储类型为设备存储时，该字段生效，中心存储会一次性返回全部片段。|
|`expand`|`body`|`string`|否|扩展内容，格式：key=value，|
|`streamform`|`body`|`string`|否|输出码流转封装格式，“ps”:PS封装格式、“rtp”:RTP封装协议。当protocol=rtsp时生效，且不传值时默认为RTP封装协议|
|`lockType`|`body`|`integer`|否|查询录像的锁定类型，0-查询全部录像；1-查询未锁定录像；2-查询已锁定录像，不传默认值为0。通过录像锁定与解锁接口来进行录像锁定与解锁。|

补充说明:
- 1：设备存储
- 默认为中心存储
- 1:TCP
- 默认为tcp，在protocol设置为rtsp或者rtmp时有效
- 注：EHOME设备回放只支持TCP传输
- GB28181 2011及以前版本只支持UDP传输
- 例如北京时间：
- 2017-06-14T00:00:00.000+08:00，参考附录BISO8601时间格式说明
- （IOS8601格式：yyyy-MM-dd’T’HH:mm:ss.SSSXXX）例如北京时间：
- 2017-06-15T00:00:00.000+08:00，参考附录BISO8601时间格式说明
- 调用方根据其播放控件支持的解码格式选择相应的封装类型；
- 支持的内容详见附录F expand扩展内容说明

## 请求参数示例
```json
{
  "cameraIndexCode": "90ad77d8057c43dab140b77361606927",
  "recordLocation": "0",
  "protocol": "rtsp",
  "transmode": 0,
  "beginTime": "2017-06-15T00:00:00.000+08:00",
  "endTime": "2017-06-18T00:00:00.000+08:00",
  "uuid": "4750e3a4a5bbad3cda5bbad3cd4af9ed5101",
  "expand": "streamform=rtp",
  "streamform": "ps",
  "lockType": 0
}
```

## 返回参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`code`|`body`|`string`|否|返回码，0 – 成功，其他- 失败，参考附录E.1.1 视频应用错误码|
|`msg`|`body`|`string`|否|返回描述|
|`data`|`body`|`object`|否|返回数据|
|`+list`|`body`|`object[]`|否|录像片段信息|
|`++lockType`|`body`|`number`|否|查询录像的锁定类型，0-全部录像；1-未锁定录像；2-已锁定录像。|
|`++beginTime`|`body`|`string`|否|开始时间|
|`++endTime`|`body`|`string`|否|结束时间|
|`++size`|`body`|`number`|否|录像片段大小|
|`+uuid`|`body`|`string`|否|分页标记|
|`+url`|`body`|`string`|否|取流短url，注：rtsp的回放url后面要指定?playBackMode=1 在vlc上才能播放|

补充说明:
- 录像片段的开始时间（IOS8601格式yyyy-MM-dd’T’HH:mm:ss.SSSzzz），参考附录BISO8601时间格式说明
- 录像片段的开始时间（IOS8601格式yyyy-MM-dd’T’HH:mm:ss.SSSzzz），参考附录BISO8601时间格式说明
- 录像片段大小（单位：Byte）
- 标记本次查询的全部标识符，用于查询分片时的多次查询

## 返回参数示例
```json
{
  "code": "0",
  "msg": "success",
  "data": {
    "list": [
      {
        "lockType": 1,
        "beginTime": "2018-08-07T14:44:04.923+08:00",
        "endTime": "2018-08-07T14:54:18.183+08:00",
        "size": 66479332
      }
    ],
    "uuid": "e33421g1109046a79b6280bafb6fa5a7",
    "url": "rtsp://10.2.145.66:6304/EUrl/Dib1ErK"
  }
}
```
