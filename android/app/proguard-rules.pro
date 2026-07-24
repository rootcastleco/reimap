# Keep the JavaScript bridge interface intact for the WebView.
-keepclassmembers class com.rootcastle.reimap.** {
    @android.webkit.JavascriptInterface <methods>;
}
