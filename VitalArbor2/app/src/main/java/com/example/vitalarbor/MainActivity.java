package com.example.vitalarbor;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import org.json.JSONObject;

/**
 * MainActivity - Login Screen
 *
 * Features:
 * - User login with username/password
 * - Guest mode (no authentication)
 * - Sign up link
 * - Debug mode toggle
 * - Network communication with backend
 */
public class MainActivity extends AppCompatActivity {

    // UI Components
    private EditText usernameField;
    private EditText passwordField;
    private Button signInBtn;
    private Button guestBtn;
    private TextView signUpBtn;
    private CheckBox debugCheckBox;
    private TextView statusLabel;

    // API Client for network requests
    private ApiClient apiClient;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize API client
        apiClient = new ApiClient();

        // Initialize UI components
        initializeViews();

        // Setup event listeners
        setupListeners();
    }

    /**
     * Initialize all UI components
     */
    private void initializeViews() {
        usernameField = findViewById(R.id.usernameField);
        passwordField = findViewById(R.id.passwordField);
        signInBtn = findViewById(R.id.signInBtn);
        guestBtn = findViewById(R.id.guestBtn);
        signUpBtn = findViewById(R.id.signUpBtn);
        debugCheckBox = findViewById(R.id.debugCheckBox);
        statusLabel = findViewById(R.id.statusLabel);
    }

    /**
     * Setup all event listeners
     */
    private void setupListeners() {
        // Debug mode toggle
        debugCheckBox.setOnCheckedChangeListener((buttonView, isChecked) -> {
            apiClient.setDebugMode(isChecked);
            updateStatus(
                    isChecked ? "Debug mode enabled" : "Debug mode disabled",
                    isChecked ? 0xFF8BC34A : 0xFF888888
            );
        });

        // Sign In button
        signInBtn.setOnClickListener(v -> handleSignIn());

        // Guest mode button
        guestBtn.setOnClickListener(v -> handleGuestMode());

        // Sign Up link
        signUpBtn.setOnClickListener(v -> handleSignUp());
    }

    /**
     * Handle sign in button click
     */
    private void handleSignIn() {
        // Get input values
        String username = usernameField.getText().toString().trim();
        String password = passwordField.getText().toString();

        // Validate inputs
        if (username.isEmpty() || password.isEmpty()) {
            updateStatus("Please enter username and password!", 0xFFC83C3C);
            return;
        }

        // Disable button to prevent multiple clicks
        signInBtn.setEnabled(false);
        updateStatus("Logging in...", 0xFF3C78B4);

        // Create JSON request
        try {
            JSONObject json = new JSONObject();
            json.put("username", username);
            json.put("password", password);

            // Make API call
            apiClient.sendPost("/login", json, new ApiClient.ApiCallback() {
                @Override
                public void onSuccess(String response) {
                    runOnUiThread(() -> {
                        signInBtn.setEnabled(true);

                        // Check if login was successful
                        if (!response.contains("error")) {
                            updateStatus("Login successful!", 0xFF4CAF50);

                            // Open dashboard
                            openDashboard(username, password);
                        } else {
                            updateStatus("Login failed - check credentials", 0xFFC83C3C);
                        }
                    });
                }

                @Override
                public void onError(String error) {
                    runOnUiThread(() -> {
                        signInBtn.setEnabled(true);
                        updateStatus("Error: " + error, 0xFFC83C3C);
                    });
                }
            });
        } catch (Exception e) {
            signInBtn.setEnabled(true);
            updateStatus("Error: " + e.getMessage(), 0xFFC83C3C);
        }
    }

    /**
     * Handle guest mode button click
     */
    private void handleGuestMode() {
        updateStatus("Opening guest dashboard...", 0xFF8BC34A);
        openDashboard("Guest", null);
    }

    /**
     * Handle sign up link click
     */
    private void handleSignUp() {
        Intent intent = new Intent(MainActivity.this, SignUpActivity.class);
        startActivity(intent);
    }

    /**
     * Update status label with message and color
     *
     * @param message Status message to display
     * @param color Color code (0xAARRGGBB format)
     */
    private void updateStatus(String message, int color) {
        statusLabel.setText(message);
        statusLabel.setTextColor(color);
    }

    /**
     * Open dashboard activity with credentials
     *
     * @param username User's username
     * @param password User's password (null for guest)
     */
    private void openDashboard(String username, String password) {
        Intent intent = new Intent(MainActivity.this, DashboardActivity.class);
        intent.putExtra("username", username);
        intent.putExtra("password", password);
        startActivity(intent);

        // Optional: Clear fields after successful login
        // usernameField.setText("");
        // passwordField.setText("");
    }

    /**
     * Called when activity is resumed (e.g., returning from sign up)
     */
    @Override
    protected void onResume() {
        super.onResume();
        // Re-enable sign in button if it was disabled
        signInBtn.setEnabled(true);
        // Clear any error messages
        if (statusLabel.getText().toString().contains("Error") ||
                statusLabel.getText().toString().contains("failed")) {
            statusLabel.setText("");
        }
    }

    /**
     * Handle back button press - deprecated method replaced
     */
    public void onBackPressedDispatcher() {
        // Show confirmation dialog before exiting app
        new AlertDialog.Builder(this)
                .setTitle("Exit App")
                .setMessage("Are you sure you want to exit VitalArbor?")
                .setPositiveButton("Yes", (dialog, which) -> {
                    super.getOnBackPressedDispatcher();
                    finish();
                })
                .setNegativeButton("No", null)
                .show();
    }
}