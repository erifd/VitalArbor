package com.example.vitalarbor;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.widget.*;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.content.FileProvider;
import org.json.JSONObject;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * DiagnosisActivity - Upload 3 tree images and run diagnosis
 */
public class DiagnosisActivity extends AppCompatActivity {

    private static final int REQUEST_IMAGE_1 = 1;
    private static final int REQUEST_IMAGE_2 = 2;
    private static final int REQUEST_IMAGE_3 = 3;
    private static final int REQUEST_CAMERA_1 = 11;
    private static final int REQUEST_CAMERA_2 = 12;
    private static final int REQUEST_CAMERA_3 = 13;
    private static final int PERMISSION_REQUEST = 100;

    private String username, password;
    private ImageView[] imageViews = new ImageView[3];
    private TextView[] imageLabels = new TextView[3];
    private File[] selectedFiles = new File[3];
    private Uri[] photoUris = new Uri[3];
    private CheckBox useCutoutCheck;
    private Spinner methodSpinner;
    private Button diagnoseBtn;
    private TextView progressLabel;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_diagnosis);

        username = getIntent().getStringExtra("username");
        password = getIntent().getStringExtra("password");

        // Initialize views
        imageViews[0] = findViewById(R.id.imageView1);
        imageViews[1] = findViewById(R.id.imageView2);
        imageViews[2] = findViewById(R.id.imageView3);
        imageLabels[0] = findViewById(R.id.imageLabel1);
        imageLabels[1] = findViewById(R.id.imageLabel2);
        imageLabels[2] = findViewById(R.id.imageLabel3);

        useCutoutCheck = findViewById(R.id.useCutoutCheck);
        methodSpinner = findViewById(R.id.methodSpinner);
        diagnoseBtn = findViewById(R.id.diagnoseBtn);
        progressLabel = findViewById(R.id.progressLabel);

        // Setup spinner
        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(this,
                R.array.detection_methods, android.R.layout.simple_spinner_item);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        methodSpinner.setAdapter(adapter);

        // Check permissions
        checkPermissions();

        // Image selection listeners
        findViewById(R.id.selectBtn1).setOnClickListener(v -> showImageSourceDialog(0));
        findViewById(R.id.selectBtn2).setOnClickListener(v -> showImageSourceDialog(1));
        findViewById(R.id.selectBtn3).setOnClickListener(v -> showImageSourceDialog(2));

        // Diagnose button
        diagnoseBtn.setOnClickListener(v -> startDiagnosis());
    }

    private void checkPermissions() {
        String[] permissions = {
                Manifest.permission.CAMERA,
                Manifest.permission.READ_EXTERNAL_STORAGE,
                Manifest.permission.WRITE_EXTERNAL_STORAGE
        };

        boolean needsPermission = false;
        for (String permission : permissions) {
            if (ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED) {
                needsPermission = true;
                break;
            }
        }

        if (needsPermission) {
            ActivityCompat.requestPermissions(this, permissions, PERMISSION_REQUEST);
        }
    }

    private void showImageSourceDialog(int index) {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Select Image Source");
        builder.setItems(new String[]{"Camera", "Gallery"}, (dialog, which) -> {
            if (which == 0) {
                takePhoto(index);
            } else {
                selectFromGallery(index);
            }
        });
        builder.show();
    }

    private void takePhoto(int index) {
        Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        if (takePictureIntent.resolveActivity(getPackageManager()) != null) {
            File photoFile = null;
            try {
                photoFile = createImageFile(index);
            } catch (IOException ex) {
                Toast.makeText(this, "Error creating file", Toast.LENGTH_SHORT).show();
            }

            if (photoFile != null) {
                Uri photoURI = FileProvider.getUriForFile(this,
                        "com.example.vitalarbor.fileprovider", photoFile);
                photoUris[index] = photoURI;
                selectedFiles[index] = photoFile;
                takePictureIntent.putExtra(MediaStore.EXTRA_OUTPUT, photoURI);
                startActivityForResult(takePictureIntent, REQUEST_CAMERA_1 + index);
            }
        }
    }

    private File createImageFile(int index) throws IOException {
        String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
        String imageFileName = "JPEG_" + timeStamp + "_" + index;
        File storageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        return File.createTempFile(imageFileName, ".jpg", storageDir);
    }

    private void selectFromGallery(int index) {
        Intent intent = new Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        startActivityForResult(intent, REQUEST_IMAGE_1 + index);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode == RESULT_OK) {
            int index = -1;
            boolean isCamera = false;

            if (requestCode >= REQUEST_CAMERA_1 && requestCode <= REQUEST_CAMERA_3) {
                index = requestCode - REQUEST_CAMERA_1;
                isCamera = true;
            } else if (requestCode >= REQUEST_IMAGE_1 && requestCode <= REQUEST_IMAGE_3) {
                index = requestCode - REQUEST_IMAGE_1;
            }

            if (index >= 0 && index < 3) {
                if (!isCamera && data != null) {
                    Uri selectedImageUri = data.getData();
                    try {
                        String path = getPathFromUri(selectedImageUri);
                        if (path != null) {
                            selectedFiles[index] = new File(path);
                        }
                    } catch (Exception e) {
                        Toast.makeText(this, "Error loading image", Toast.LENGTH_SHORT).show();
                        return;
                    }
                }

                // Update UI
                if (selectedFiles[index] != null) {
                    Bitmap bitmap = BitmapFactory.decodeFile(selectedFiles[index].getAbsolutePath());
                    imageViews[index].setImageBitmap(bitmap);
                    imageLabels[index].setText("✓ " + selectedFiles[index].getName());
                }
            }
        }
    }

    private String getPathFromUri(Uri uri) {
        String[] projection = {MediaStore.Images.Media.DATA};
        android.database.Cursor cursor = getContentResolver().query(uri, projection, null, null, null);
        if (cursor != null) {
            int columnIndex = cursor.getColumnIndexOrThrow(MediaStore.Images.Media.DATA);
            cursor.moveToFirst();
            String path = cursor.getString(columnIndex);
            cursor.close();
            return path;
        }
        return null;
    }

    private void startDiagnosis() {
        // Validate
        int count = 0;
        for (File f : selectedFiles) {
            if (f != null) count++;
        }

        if (count < 3) {
            Toast.makeText(this, "Please select all 3 images!", Toast.LENGTH_SHORT).show();
            return;
        }

        // Show progress
        diagnoseBtn.setEnabled(false);
        progressLabel.setText("Uploading images and running analysis...");
        progressLabel.setVisibility(android.view.View.VISIBLE);

        // Run diagnosis on background thread
        new Thread(() -> {
            try {
                // Upload all 3 images with diagnosis endpoint
                String boundary = "----VitalArborBoundary" + System.currentTimeMillis();
                URL url = new URL("http://10.0.2.2:3000/api/diagnose");  // Change for real device

                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setDoInput(true);
                conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
                conn.setConnectTimeout(300000);  // 5 minutes
                conn.setReadTimeout(300000);

                try (OutputStream os = conn.getOutputStream();
                     PrintWriter writer = new PrintWriter(new OutputStreamWriter(os, StandardCharsets.UTF_8), true)) {

                    // Username
                    writer.append("--").append(boundary).append("\r\n");
                    writer.append("Content-Disposition: form-data; name=\"username\"\r\n\r\n");
                    writer.append(username).append("\r\n");

                    // Password
                    writer.append("--").append(boundary).append("\r\n");
                    writer.append("Content-Disposition: form-data; name=\"password\"\r\n\r\n");
                    writer.append(password).append("\r\n");

                    // Use cutout
                    writer.append("--").append(boundary).append("\r\n");
                    writer.append("Content-Disposition: form-data; name=\"useCutout\"\r\n\r\n");
                    writer.append(useCutoutCheck.isChecked() ? "true" : "false").append("\r\n");

                    // Detection method
                    writer.append("--").append(boundary).append("\r\n");
                    writer.append("Content-Disposition: form-data; name=\"detectionMethod\"\r\n\r\n");
                    writer.append(String.valueOf(methodSpinner.getSelectedItemPosition() + 1)).append("\r\n");

                    // Classification image
                    writeFileToMultipart(writer, os, boundary, "classification", selectedFiles[0]);

                    // Tilt image
                    writeFileToMultipart(writer, os, boundary, "tilt", selectedFiles[1]);

                    // Backup image
                    writeFileToMultipart(writer, os, boundary, "backup", selectedFiles[2]);

                    // End
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

                runOnUiThread(() -> {
                    diagnoseBtn.setEnabled(true);
                    progressLabel.setVisibility(android.view.View.GONE);

                    if (status >= 200 && status < 300) {
                        // Parse JSON response
                        try {
                            JSONObject jsonResponse = new JSONObject(responseStr);
                            JSONObject results = jsonResponse.getJSONObject("results");

                            Intent intent = new Intent(DiagnosisActivity.this, ResultsActivity.class);
                            intent.putExtra("imagePath", selectedFiles[0].getAbsolutePath());
                            intent.putExtra("riskScore", results.getString("riskScore"));
                            intent.putExtra("riskCategory", results.getString("riskCategory"));
                            intent.putExtra("tiltAngle", results.getString("tiltAngle"));
                            intent.putExtra("species", results.getString("species"));
                            intent.putExtra("diagnosis", results.getString("diagnosis"));
                            intent.putExtra("fixes", results.getString("fixes"));
                            startActivity(intent);
                        } catch (Exception e) {
                            Toast.makeText(this, "Error parsing results: " + e.getMessage(),
                                    Toast.LENGTH_LONG).show();
                        }
                    } else {
                        Toast.makeText(this, "Error: " + responseStr, Toast.LENGTH_LONG).show();
                    }
                });

            } catch (Exception e) {
                runOnUiThread(() -> {
                    diagnoseBtn.setEnabled(true);
                    progressLabel.setVisibility(android.view.View.GONE);
                    Toast.makeText(this, "Network error: " + e.getMessage(),
                            Toast.LENGTH_LONG).show();
                });
            }
        }).start();
    }

    private void writeFileToMultipart(PrintWriter writer, OutputStream os, String boundary,
                                      String fieldName, File file) throws IOException {
        writer.append("--").append(boundary).append("\r\n");
        writer.append("Content-Disposition: form-data; name=\"").append(fieldName)
                .append("\"; filename=\"").append(file.getName()).append("\"\r\n");
        writer.append("Content-Type: image/jpeg\r\n");
        writer.append("Content-Transfer-Encoding: binary\r\n\r\n");
        writer.flush();

        try (FileInputStream fis = new FileInputStream(file)) {
            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = fis.read(buffer)) != -1) {
                os.write(buffer, 0, bytesRead);
            }
        }
        os.flush();

        writer.append("\r\n");
        writer.flush();
    }
}