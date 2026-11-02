# 测试环境

测试组在 AWS Device Farm（us-west-2）上做真机测试，资源如下。

| 项 | 值 |
|---|---|
| Device Farm 项目 | `arn:aws:devicefarm:us-west-2:111122223333:project:3fa85f64-5717-4562-b3fc-2c963f66afa6` |
| Android 手机 | Pixel 8a（Android 14），设备 ARN `arn:aws:devicefarm:us-west-2::device:5F2D9B1C7A3E4D6F8B0A1C2D3E4F5A6B` |
| 放安装包的 S3 桶 | `shop-qa-apps`（us-east-1） |

应用包名 `com.example.shop`。每个设备 scope 开一个远程访问会话，按设备分钟计费。
