# 示例商城 iPhone 客户端

商城的 iPhone 客户端，bundle id `com.example.ShopDemo`。测试组拿到的真机安装包在 `build/ShopDemo.ipa`（Ad Hoc 签名）。

## DeepLink

应用在 Info.plist 里注册了 `shopdemo` scheme，支持两种地址：

- `shopdemo://coupons`：打开优惠券中心。
- `shopdemo://product/<商品 id>`：打开该商品的详情页。

## 首页搜索

首页顶部是搜索框，右侧有「搜索」按钮；键盘弹出时按钮仍在键盘上方、可以点到。键盘的回车键显示为「搜索」，按下即提交。

## 手机版网页

手机版网页在 https://m.shop.example.test/ ，搜索结果页的地址是 `https://m.shop.example.test/search?q=<关键词>`。

桌面网页版的用例在 `features/shop_web.feature`，确定性 step 在 `steps/`。
