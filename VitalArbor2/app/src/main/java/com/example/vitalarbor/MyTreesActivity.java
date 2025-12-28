package com.example.vitalarbor;

import android.os.Bundle;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import org.json.JSONObject;

class MyTreesActivity extends AppCompatActivity {
    private String username, password;
    private TextView treesText;
    private ApiClient apiClient;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_my_trees);

        username = getIntent().getStringExtra("username");
        password = getIntent().getStringExtra("password");

        apiClient = new ApiClient();
        treesText = findViewById(R.id.treesText);

        loadTrees();
    }

    private void loadTrees() {
        treesText.setText("Loading your trees...");

        try {
            JSONObject json = new JSONObject();
            json.put("username", username);
            json.put("password", password);

            apiClient.sendPost("/images", json, new ApiClient.ApiCallback() {
                @Override
                public void onSuccess(String response) {
                    runOnUiThread(() -> {
                        if (response.contains("\"images\":[]")) {
                            treesText.setText("No images found.\n\nUpload your first tree image to get started!");
                        } else if (response.contains("\"images\":[")) {
                            int count = response.split("\"url\":").length - 1;
                            treesText.setText(String.format("Found %d image(s) in your account!\n\n" +
                                            "Your images are stored in Firebase Storage.\n\nResponse data:\n%s",
                                    count, response));
                        } else {
                            treesText.setText("Response: " + response);
                        }
                    });
                }

                @Override
                public void onError(String error) {
                    runOnUiThread(() -> treesText.setText("Error loading images:\n" + error));
                }
            });
        } catch (Exception e) {
            treesText.setText("Error: " + e.getMessage());
        }
    }
}