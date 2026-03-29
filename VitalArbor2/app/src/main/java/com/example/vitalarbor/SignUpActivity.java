package com.example.vitalarbor;

import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import org.json.JSONObject;

/**
 * SignUpActivity - User Registration Screen
 */
public class SignUpActivity extends AppCompatActivity {

    private EditText usernameField;
    private EditText passwordField;
    private Button signUpBtn;
    private ApiClient apiClient;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_signup);

        apiClient = new ApiClient();

        // Initialize views
        usernameField = findViewById(R.id.usernameField);
        passwordField = findViewById(R.id.passwordField);
        signUpBtn = findViewById(R.id.signUpBtn);

        // Sign Up button
        signUpBtn.setOnClickListener(v -> handleSignUp());
    }

    private void handleSignUp() {
        String username = usernameField.getText().toString().trim();
        String password = passwordField.getText().toString();

        // Validate
        if (username.isEmpty() || password.isEmpty()) {
            Toast.makeText(this, "Please fill all fields!", Toast.LENGTH_SHORT).show();
            return;
        }

        if (password.length() < 6) {
            Toast.makeText(this, "Password must be at least 6 characters!", Toast.LENGTH_SHORT).show();
            return;
        }

        signUpBtn.setEnabled(false);

        try {
            JSONObject json = new JSONObject();
            json.put("username", username);
            json.put("password", password);

            apiClient.sendPost("/signup", json, new ApiClient.ApiCallback() {
                @Override
                public void onSuccess(String response) {
                    runOnUiThread(() -> {
                        signUpBtn.setEnabled(true);
                        if (!response.contains("error")) {
                            Toast.makeText(SignUpActivity.this,
                                    "Account created! You can now login.",
                                    Toast.LENGTH_SHORT).show();
                            finish();
                        } else if (response.contains("already exists")) {
                            Toast.makeText(SignUpActivity.this,
                                    "Username already taken!",
                                    Toast.LENGTH_SHORT).show();
                        } else {
                            Toast.makeText(SignUpActivity.this,
                                    "Error creating account!",
                                    Toast.LENGTH_SHORT).show();
                        }
                    });
                }

                @Override
                public void onError(String error) {
                    runOnUiThread(() -> {
                        signUpBtn.setEnabled(true);
                        Toast.makeText(SignUpActivity.this,
                                "Error: " + error,
                                Toast.LENGTH_SHORT).show();
                    });
                }
            });
        } catch (Exception e) {
            signUpBtn.setEnabled(true);
            Toast.makeText(this, "Error: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }
}