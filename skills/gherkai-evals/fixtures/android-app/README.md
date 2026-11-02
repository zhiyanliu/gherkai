# 示例商城 Android 客户端

商城的 Android 客户端，包名 `com.example.shop`。测试组拿到的安装包放在 `app/shop-demo.apk`。

## DeepLink

应用注册了 `shop` scheme，支持两种地址：

- `shop://product/<商品 id>`：打开该商品的详情页。
- `shop://search?q=<关键词>`：打开该关键词的搜索结果页。

网页版商城的用例在 `features/shop_web.feature`，确定性 step 在 `steps/`。
