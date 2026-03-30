# 获取监控点预览取流URLv2

> 接口说明
> 1.平台正常运行；平台已经添加过设备和监控点信息。
> 2.平台需要安装mgc取流服务。
> 3.三方平台通过openAPI获取到监控点数据，依据自身业务开发监控点导航界面。
> 4.调用本接口获取预览取流URL，协议类型包括：hik、rtsp、rtmp、hls、ws。
> 5.通过开放平台的开发包进行实时预览或者使用标准的GUI播放工具进行实时预览。
> 6.为保证数据的安全性，取流URL设有有效时间，有效时间为5分钟。

## 基本信息
|项目|值|
|---|---|
|接口版本|v2|
|适配版本|综合安防管理平台iSecure Center V1.4及以上版本|
|接口地址|`/api/video/v2/cameras/previewURLs`|
|请求方法|`POST`|
|数据提交方式|application/json|

## 快速调用
```text
POST /api/video/v2/cameras/previewURLs
```

## 请求参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`cameraIndexCode`|`body`|`string`|是|监控点唯一标识，分页获取监控点资源接口获取返回参数cameraIndexCode|
|`streamType`|`body`|`integer`|否|码流类型，0:主码流|
|`protocol`|`body`|`string`|否|取流协议（应用层协议）。 “hik”:HIK私有协议，使用视频SDK进行播放时，传入此类型；“rtsp”:RTSP协议；“rtmp”:RTMP协议；“hls”:HLS协议；“hlss”:基于ssl/tls的HLS协议；“ws”:Websocket协议；“wss”:基于ssl/tls的Websocket协议；“httpflv”:HTTP-FLV协议；“httpsflv”:基于ssl/tls的HTTP-FLV协议。 参数不填，默认为HIK协议，最大长度：64。 注： 1、HLS协议只支持海康SDK协议、EHOME协议、ONVIF协议接入的设备；只支持H264、H265视频编码和AAC音频编码； 2、Websocket协议仅限使用H5视频播放器取流播放 3、HTTP-FLV协议只支持海康SDK协议、EHOME协议、ONVIF协议接入的设备；只支持H264、h265视频编码和AAC音频编码。|
|`transmode`|`body`|`integer`|否|传输协议（传输层协议），0:UDP|
|`expand`|`body`|`string`|否|标识扩展内容，格式：key=value，|
|`streamform`|`body`|`string`|否|输出码流转封装格式，“ps”:PS封装格式、“rtp”:RTP封装协议。当protocol=rtsp时生效，且不传值时默认为RTP封装协议。|

补充说明:
- 1:子码流
- 2:第三码流
- 参数不填，默认为主码流
- 1:TCP
- 默认是TCP
- 注：
- GB28181 2011及以前版本只支持UDP传输
- 调用方根据其播放控件支持的解码格式选择相应的封装类型；
- 支持的内容详见附录F expand扩展内容说明

## 请求参数示例
```json
{
  "cameraIndexCode": "748d84750e3a4a5bbad3cd4af9ed5101",
  "streamType": 0,
  "protocol": "rtsp",
  "transmode": 1,
  "expand": "transcode=0",
  "streamform": "ps"
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
    "url": "rtsp://10.2.145.66:655/EUrl/CLJ52BW"
  }
}
```
