package com.ffmod;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;

public class OverlayService extends Service {

    private static final String CHANNEL_ID = "ffmod_overlay";
    private WindowManager windowManager;
    private View overlayRoot;
    private WindowManager.LayoutParams params;

    // drag state
    private int initialX, initialY;
    private float initialTouchX, initialTouchY;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        Notification notif = new Notification.Builder(this, CHANNEL_ID)
                .setContentTitle("FF Mod Menu Active")
                .setContentText("Overlay running")
                .setSmallIcon(android.R.drawable.ic_menu_view)
                .build();
        startForeground(1, notif);

        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        setupOverlay();
    }

    private void setupOverlay() {
        // The overlay itself is rendered by Kivy's NativeView in Python.
        // This Java service only manages the WindowManager layout params
        // so the Kivy window can sit on top of the game.

        params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                        ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                        : WindowManager.LayoutParams.TYPE_PHONE,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                        | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT
        );
        params.gravity = Gravity.TOP | Gravity.START;
        params.x = 20;
        params.y = 200;

        // Minimal floating button — tap expands the Kivy panel
        overlayRoot = new View(this);
        overlayRoot.setBackgroundColor(Color.argb(200, 20, 20, 30));

        overlayRoot.setOnTouchListener((v, event) -> {
            switch (event.getAction()) {
                case MotionEvent.ACTION_DOWN:
                    initialX = params.x;
                    initialY = params.y;
                    initialTouchX = event.getRawX();
                    initialTouchY = event.getRawY();
                    return true;
                case MotionEvent.ACTION_MOVE:
                    params.x = initialX + (int)(event.getRawX() - initialTouchX);
                    params.y = initialY + (int)(event.getRawY() - initialTouchY);
                    windowManager.updateViewLayout(overlayRoot, params);
                    return true;
            }
            return false;
        });

        windowManager.addView(overlayRoot, params);
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel ch = new NotificationChannel(
                    CHANNEL_ID, "FF Mod Overlay",
                    NotificationManager.IMPORTANCE_LOW
            );
            ch.setDescription("Floating mod menu overlay");
            NotificationManager nm = getSystemService(NotificationManager.class);
            nm.createNotificationChannel(ch);
        }
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (overlayRoot != null) windowManager.removeView(overlayRoot);
    }
}
