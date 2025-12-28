package com.example.vitalarbor;

import android.util.Log;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * ApiClient - Handles all network communication with backend
 *
 * Features:
 * - POST requests with JSON
 * - Image upload with multipart/form-data
 * - Async callbacks
 * - Debug logging
 */
public class ApiClient {
    private static final String TAG = "ApiClient";

    // Backend URL - Change based on your setup
    // For Android Emulator connecting to localhost
    private static final String BASE_URL = "http://10.0.2.2:3000/api";

    // For Real Android Device - Replace XXX.XXX.XXX.XXX with your computer's IP
    // Find it with: ipconfig (Windows) or ifconfig (Mac/Linux)
    // Example: private static final String BASE_URL = "http://192.168.1.105:3000/api";

    private boolean debugMode = false;

    /**
     * Enable or disable debug logging
     */
    public void setDebugMode(boolean debug) {
        this.debugMode = debug;
        if (debug) {
            Log.d(TAG, "Debug mode enabled");
            Log.d(TAG, "Backend URL: " + BASE_URL);
        }
    }

    /**
     * Callback interface for async API responses
     */
    public interface ApiCallback {
        void onSuccess(String response);
        void onError(String error);
    }

    /**
     * Send POST request with JSON data
     *
     * @param endpoint API endpoint (e.g., "/login", "/signup")
     * @param jsonData JSON object to send
     * @param callback Response callback
     */
    public void sendPost(String endpoint, JSONObject jsonData, ApiCallback callback) {
        new Thread(() -> {
            try {
                URL url = new URL(BASE_URL + endpoint);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setRequestProperty("Accept", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(10000);
                conn.setReadTimeout(10000);

                if (debugMode) {
                    Log.d(TAG, "POST Request to: " + BASE_URL + endpoint);
                    Log.d(TAG, "Request body: " + jsonData.toString());
                }

                // Write JSON data
                try (OutputStream os = conn.getOutputStream()) {
                    byte[] input = jsonData.toString().getBytes(StandardCharsets.UTF_8);
                    os.write(input, 0, input.length);
                }

                // Read response
                int status = conn.getResponseCode();
                InputStream is = (status < 400) ? conn.getInputStream() : conn.getErrorStream();

                StringBuilder response = new StringBuilder();
                try (BufferedReader br = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = br.readLine()) != null) {
                        response.append(line.trim());
                    }
                }

                String responseStr = response.toString();

                if (debugMode) {
                    Log.d(TAG, "Response status: " + status);
                    Log.d(TAG, "Response body: " + responseStr);
                }

                if (status >= 200 && status < 300) {
                    callback.onSuccess(responseStr);
                } else {
                    callback.onError("HTTP " + status + ": " + responseStr);
                }

            } catch (Exception e) {
                Log.e(TAG, "Network error", e);
                callback.onError("Network error: " + e.getMessage());
            }
        }).start();
    }

    /**
     * Upload image file with authentication
     *
     * @param imageFile Image file to upload
     * @param username User's username
     * @param password User's password
     * @param callback Response callback
     */
    public void uploadImage(File imageFile, String username, String password, ApiCallback callback) {
        new Thread(() -> {
            try {
                String boundary = "----VitalArborBoundary" + System.currentTimeMillis();
                URL url = new URL(BASE_URL + "/upload");

                if (debugMode) {
                    Log.d(TAG, "Uploading image: " + imageFile.getName());
                    Log.d(TAG, "File size: " + imageFile.length() + " bytes");
                }

                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setDoInput(true);
                conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
                conn.setConnectTimeout(30000);
                conn.setReadTimeout(30000);

                try (OutputStream os = conn.getOutputStream();
                     PrintWriter writer = new PrintWriter(new OutputStreamWriter(os, StandardCharsets.UTF_8), true)) {

                    // Username field
                    writer.append("--").append(boundary).append("\r\n");
                    writer.append("Content-Disposition: form-data; name=\"username\"\r\n\r\n");
                    writer.append(username).append("\r\n");
                    writer.flush();

                    // Password field
                    writer.append("--").append(boundary).append("\r\n");
                    writer.append("Content-Disposition: form-data; name=\"password\"\r\n\r\n");
                    writer.append(password).append("\r\n");
                    writer.flush();

                    // Image file
                    writer.append("--").append(boundary).append("\r\n");
                    writer.append("Content-Disposition: form-data; name=\"image\"; filename=\"")
                            .append(imageFile.getName()).append("\"\r\n");

                    String contentType = "application/octet-stream";
                    String fileName = imageFile.getName().toLowerCase();
                    if (fileName.endsWith(".jpg") || fileName.endsWith(".jpeg")) {
                        contentType = "image/jpeg";
                    } else if (fileName.endsWith(".png")) {
                        contentType = "image/png";
                    }

                    writer.append("Content-Type: ").append(contentType).append("\r\n");
                    writer.append("Content-Transfer-Encoding: binary\r\n\r\n");
                    writer.flush();

                    // Write image bytes
                    try (FileInputStream fis = new FileInputStream(imageFile)) {
                        byte[] buffer = new byte[4096];
                        int bytesRead;
                        while ((bytesRead = fis.read(buffer)) != -1) {
                            os.write(buffer, 0, bytesRead);
                        }
                    }
                    os.flush();

                    writer.append("\r\n");
                    writer.append("--").append(boundary).append("--\r\n");
                    writer.flush();
                }

                int status = conn.getResponseCode();
                InputStream is = (status < 400) ? conn.getInputStream() : conn.getErrorStream();
                StringBuilder response = new StringBuilder();

                try (BufferedReader br = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = br.readLine()) != null) {
                        response.append(line);
                    }
                }

                String responseStr = response.toString();

                if (debugMode) {
                    Log.d(TAG, "Upload response status: " + status);
                    Log.d(TAG, "Upload response: " + responseStr);
                }

                if (status >= 200 && status < 300) {
                    callback.onSuccess(responseStr);
                } else {
                    callback.onError("Upload failed: " + responseStr);
                }

            } catch (Exception e) {
                Log.e(TAG, "Upload error", e);
                callback.onError("Upload error: " + e.getMessage());
            }
        }).start();
    }
}