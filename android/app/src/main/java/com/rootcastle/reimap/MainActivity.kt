package com.rootcastle.reimap

import android.annotation.SuppressLint
import android.os.Bundle
import android.text.InputType
import android.view.Menu
import android.view.MenuItem
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity

/**
 * reimap Android host.
 *
 * The app is a thin, hardened WebView shell around two experiences:
 *
 *  1. **Offline demo** (default) — a fully self-contained animated world map
 *     bundled in `assets/demo/`. It needs no server and no network, which makes
 *     the app runnable and shareable the instant it is installed.
 *  2. **Live view** — point the app at a reimap desktop/server instance
 *     (`http://host:port`) to stream the real connections your machine makes.
 *
 * The desktop engine does the privileged socket scanning; the phone renders. This
 * keeps the Android build small, permission-light, and store-friendly.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView

    private val prefs by lazy { getSharedPreferences("reimap", MODE_PRIVATE) }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        web = WebView(this)
        setContentView(web)

        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            loadWithOverviewMode = true
            useWideViewPort = true
            cacheMode = android.webkit.WebSettings.LOAD_DEFAULT
        }
        web.webViewClient = WebViewClient()

        loadStartDestination()
    }

    private fun loadStartDestination() {
        val server = prefs.getString("server", null)
        if (server.isNullOrBlank()) {
            web.loadUrl(DEMO_URL)
        } else {
            web.loadUrl(server)
        }
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menu.add(0, MENU_DEMO, 0, getString(R.string.menu_demo))
        menu.add(0, MENU_CONNECT, 1, getString(R.string.menu_connect))
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            MENU_DEMO -> {
                prefs.edit().remove("server").apply()
                web.loadUrl(DEMO_URL)
                true
            }
            MENU_CONNECT -> {
                showConnectDialog()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    /** Prompt for a reimap server URL and load it. */
    private fun showConnectDialog() {
        val input = EditText(this).apply {
            inputType = InputType.TYPE_TEXT_VARIATION_URI
            hint = "http://192.168.1.10:8050"
            setText(prefs.getString("server", "http://"))
        }
        AlertDialog.Builder(this)
            .setTitle(R.string.connect_title)
            .setMessage(R.string.connect_message)
            .setView(input)
            .setPositiveButton(R.string.connect_ok) { _, _ ->
                val url = input.text.toString().trim()
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    prefs.edit().putString("server", url).apply()
                    web.loadUrl(url)
                } else {
                    Toast.makeText(this, R.string.connect_invalid, Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton(R.string.connect_cancel, null)
            .show()
    }

    /** Let the hardware back button navigate WebView history first. */
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }

    private companion object {
        const val DEMO_URL = "file:///android_asset/demo/index.html"
        const val MENU_DEMO = 1
        const val MENU_CONNECT = 2
    }
}
