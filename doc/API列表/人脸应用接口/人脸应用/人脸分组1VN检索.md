# 人脸分组1VN检索

> 接口说明
> a)1VN人脸分组检索是将任意人脸图片与人脸分组中的人脸照片进行比对，以确认是人脸分组中的哪一个人。
> b)检索的人脸分组必须配置有识别计划，否则将无法进行检索。
> c)检索出来的结果是分页的集合，单个识别资源最多可以检索100条记录。
> d)必须指定搜图的分组范围，且最多可以在16个分组内搜索。
> e)图片格式仅支持JGP，图片大小为128B到4M。
> f)注：支持设备：sdk超脑、脸谱、智能应用服务器。

## 基本信息
|项目|值|
|---|---|
|接口版本|v1|
|适配版本|综合安防管理平台iSecure Center V1.4及以上版本|
|接口地址|`/api/frs/v1/application/oneToMany`|
|请求方法|`POST`|
|数据提交方式|application/json|

## 快速调用
```text
POST /api/frs/v1/application/oneToMany
```

## 请求参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`pageNo`|`body`|`integer`|是|分页查询条件，页码，为空时，等价于1，页码不能小于1|
|`pageSize`|`body`|`integer`|是|分页查询条件，页尺，为空时，等价于1000，页尺不能小于1或大于1000|
|`searchNum`|`body`|`integer`|否|指定单个识别资源最大搜索张数，最大值为100，为空时，等价于100|
|`minSimilarity`|`body`|`integer`|是|指定检索的最小相似度，最小为1，最大为100。|
|`facePicUrl`|`body`|`string`|否|用于检索的图片，要求URL可以通过POST方式直接下载，该参数与facePicBinaryData至少有一个存在，都存在时优先使用facePicBinaryData|
|`facePicBinaryData`|`body`|`string`|否|用于检索的图片的二进制数据Base64编码后的字符串，该参数与facePicUrl至少有一个存在，都存在时优先使用facePicBinaryData|
|`faceGroupIndexCodes`|`body`|`string[]`|是|人脸分组唯一标志，指定检索的人脸分组范围|
|`name`|`body`|`string`|否|人脸名称模糊查询|
|`certificateType`|`body`|`string`|否|人脸的证件类别，111-身份证，OTHER-其它证件|
|`certificateNum`|`body`|`string`|否|人脸的证件号码模糊查询|

补充说明:
- 为提高比对准确率，建议相似度值设置50以上。

## 请求参数示例
```json
{
  "pageNo": 1,
  "pageSize": 20,
  "searchNum": 99,
  "minSimilarity": 50,
  "facePicUrl": "http://10.21.22.115:6120/pic?7dd43=sb6-z67194163f7=11i5m*ep",
  "facePicBinaryData": "string",
  "faceGroupIndexCodes": [
    "string"
  ],
  "name": "张",
  "certificateType": "1",
  "certificateNum": "4202041996051"
}
```

## 返回参数
|参数|位置|类型|必填|说明|
|---|---|---|---|---|
|`code`|`body`|`string`|否|返回码，0 – 成功，其他- 失败，参考附录E.5 智能监控错误码|
|`msg`|`body`|`string`|否|返回描述|
|`data`|`body`|`object`|否|从人脸分组中检索的分页结果|
|`+total`|`body`|`number`|否|结果总数|
|`+pageNo`|`body`|`number`|否|当前页|
|`+pageSize`|`body`|`number`|否|每页记录数|
|`+list`|`body`|`object[]`|否|1VN识别结果|
|`++similarity`|`body`|`number`|否|该人脸和上传人脸的相似度|
|`++indexCode`|`body`|`string`|否|人脸的唯一标识是|
|`++faceInfo`|`body`|`object`|否|人脸信息对象|
|`+++name`|`body`|`string`|否|人脸的名称|
|`+++certificateType`|`body`|`string`|否|人脸的证件类别，111-身份证，OTHER-其它证件|
|`+++certificateNum`|`body`|`string`|否|人脸的证件号码信息。1~20个数字、字母。|
|`++facePic`|`body`|`object`|否|人脸图片对象|
|`+++faceUrl`|`body`|`string`|否|查询返回时，为绝对地址|

## 返回参数示例
```json
{
  "code": "0",
  "msg": "Success.",
  "data": {
    "total": 500,
    "pageNo": 1,
    "pageSize": 10,
    "list": [
      {
        "similarity": 80,
        "indexCode": "7cc0aCC2-a3c3-48fd-b432-718103e85c28",
        "faceInfo": {
          "name": "张三",
          "certificateType": "111",
          "certificateNum": "420204199605121656"
        },
        "facePic": {
          "faceUrl": "http://10.166.165.121:8080/frs/facepicturetemp/test.JGP"
        }
      }
    ]
  }
}
```
