package com.example.vitalarbor;

import android.content.Intent;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;

/**
 * DashboardActivity - Main hub after login
 */
public class DashboardActivity extends AppCompatActivity {

    private String username;
    private String password;

    private TextView welcomeText;
    private Button logoutBtn;
    private CardView diagnosisCard;
    private CardView myTreesCard;
    private CardView speciesCard;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_dashboard);

        // Get credentials from intent
        username = getIntent().getStringExtra("username");
        password = getIntent().getStringExtra("password");

        // Initialize views
        welcomeText = findViewById(R.id.welcomeText);
        logoutBtn = findViewById(R.id.logoutBtn);
        diagnosisCard = findViewById(R.id.diagnosisCard);
        myTreesCard = findViewById(R.id.myTreesCard);
        speciesCard = findViewById(R.id.speciesCard);

        // Set welcome text
        welcomeText.setText("Welcome, " + username + "!");

        // Setup listeners
        logoutBtn.setOnClickListener(v -> {
            finish();
        });

        diagnosisCard.setOnClickListener(v -> {
            Intent intent = new Intent(DashboardActivity.this, DiagnosisActivity.class);
            intent.putExtra("username", username);
            intent.putExtra("password", password);
            startActivity(intent);
        });

        myTreesCard.setOnClickListener(v -> {
            Intent intent = new Intent(DashboardActivity.this, MyTreesActivity.class);
            intent.putExtra("username", username);
            intent.putExtra("password", password);
            startActivity(intent);
        });

        speciesCard.setOnClickListener(v -> {
            Intent intent = new Intent(DashboardActivity.this, SpeciesActivity.class);
            intent.putExtra("username", username);
            intent.putExtra("password", password);
            startActivity(intent);
        });
    }


    public void onBackPressedDispatcher() {
        // Don't go back to login, minimize app instead
        moveTaskToBack(true);
    }
}