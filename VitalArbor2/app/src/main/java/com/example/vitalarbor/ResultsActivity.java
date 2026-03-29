package com.example.vitalarbor;

import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.os.Bundle;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;

/**
 * ResultsActivity - Display color-coded diagnosis results
 */
public class ResultsActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_results);

        // Get data from intent
        String imagePath = getIntent().getStringExtra("imagePath");
        String riskScore = getIntent().getStringExtra("riskScore");
        String riskCategory = getIntent().getStringExtra("riskCategory");
        String tiltAngle = getIntent().getStringExtra("tiltAngle");
        String species = getIntent().getStringExtra("species");
        String diagnosis = getIntent().getStringExtra("diagnosis");
        String fixes = getIntent().getStringExtra("fixes");

        // Initialize views
        ImageView resultImage = findViewById(R.id.resultImage);
        TextView riskLabel = findViewById(R.id.riskLabel);
        TextView scoreLabel = findViewById(R.id.scoreLabel);
        TextView speciesText = findViewById(R.id.speciesText);
        TextView tiltText = findViewById(R.id.tiltText);
        TextView diagnosisText = findViewById(R.id.diagnosisText);
        TextView fixesText = findViewById(R.id.fixesText);
        CardView diagnosisCard = findViewById(R.id.diagnosisCard);
        Button closeBtn = findViewById(R.id.closeBtn);

        // Load image
        if (imagePath != null) {
            resultImage.setImageBitmap(BitmapFactory.decodeFile(imagePath));
        }

        // Set texts
        riskLabel.setText("Risk Level: " + (riskCategory != null ? riskCategory : "Unknown"));
        scoreLabel.setText("Score: " + (riskScore != null ? riskScore : "N/A"));
        speciesText.setText("Species: " + (species != null ? species : "N/A"));
        tiltText.setText("Tilt: " + (tiltAngle != null ? tiltAngle : "N/A"));
        diagnosisText.setText(diagnosis != null ? diagnosis : "No diagnosis available");
        fixesText.setText(fixes != null ? fixes : "No recommendations available");

        // Determine color based on risk
        int bgColor;
        String riskLower = riskCategory != null ? riskCategory.toLowerCase() : "";
        if (riskLower.contains("low") || riskLower.contains("healthy")) {
            bgColor = Color.parseColor("#4CAF50"); // Green
        } else if (riskLower.contains("medium") || riskLower.contains("moderate")) {
            bgColor = Color.parseColor("#FFC107"); // Yellow/Orange
        } else if (riskLower.contains("high") || riskLower.contains("orange")) {
            bgColor = Color.parseColor("#FF9800"); // Orange
        } else if (riskLower.contains("critical") || riskLower.contains("red")) {
            bgColor = Color.parseColor("#F44336"); // Red
        } else {
            bgColor = Color.parseColor("#9E9E9E"); // Gray
        }

        // Apply color
        diagnosisCard.setCardBackgroundColor(bgColor);
        riskLabel.setTextColor(Color.WHITE);
        scoreLabel.setTextColor(Color.WHITE);
        speciesText.setTextColor(Color.WHITE);
        tiltText.setTextColor(Color.WHITE);
        diagnosisText.setTextColor(Color.WHITE);
        fixesText.setTextColor(Color.WHITE);

        // Close button
        closeBtn.setOnClickListener(v -> finish());
    }
}