# 测试环境

测试组在 AWS Device Farm（us-west-2）上做真机测试，资源如下。

| 项 | 值 |
|---|---|
| Device Farm 项目 | `arn:aws:devicefarm:us-west-2:111122223333:project:7c9e6679-7425-40de-944b-e07fc1f90ae7` |
| iPhone | iPhone 17 Pro（iOS 26.3.1），设备 ARN `arn:aws:devicefarm:us-west-2::device:9E3C1A7B5D2F4E6A8C0B1D3F5A7C9E2B` |
| Android 组在用的手机 | Pixel 8a（Android 14），设备 ARN `arn:aws:devicefarm:us-west-2::device:5F2D9B1C7A3E4D6F8B0A1C2D3E4F5A6B` |
| 放 iOS 安装包的 S3 桶 | `shop-ios-qa-builds`（us-east-1） |
