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
import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * SpeciesActivity - Identify tree species from photo
 */
public class SpeciesActivity extends AppCompatActivity {

    private static final int REQUEST_IMAGE = 1;
    private static final int REQUEST_CAMERA = 2;
    private static final int PERMISSION_REQUEST = 100;

    private String username;
    private String password;
    private ImageView selectedImageView;
    private TextView selectedLabel;
    private Button selectBtn;
    private Button identifyBtn;
    private File selectedFile;
    private Uri photoUri;
    private ApiClient apiClient;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_species);

        username = getIntent().getStringExtra("username");
        password = getIntent().getStringExtra("password");

        apiClient = new ApiClient();

        selectedImageView = findViewById(R.id.selectedImageView);
        selectedLabel = findViewById(R.id.selectedLabel);
        selectBtn = findViewById(R.id.selectBtn);
        identifyBtn = findViewById(R.id.identifyBtn);

        checkPermissions();

        selectBtn.setOnClickListener(v -> showImageSourceDialog());

        identifyBtn.setOnClickListener(v -> {
            if (selectedFile == null) {
                Toast.makeText(this, "Please select an image first!", Toast.LENGTH_SHORT).show();
                return;
            }

            // Upload image for species identification
            identifyBtn.setEnabled(false);
            Toast.makeText(this, "Uploading image for species identification...", Toast.LENGTH_SHORT).show();

            apiClient.uploadImage(selectedFile, username, password, new ApiClient.ApiCallback() {
                @Override
                public void onSuccess(String response) {
                    runOnUiThread(() -> {
                        identifyBtn.setEnabled(true);
                        Toast.makeText(SpeciesActivity.this,
                                "Image uploaded successfully! Species identification coming soon.",
                                Toast.LENGTH_LONG).show();
                    });
                }

                @Override
                public void onError(String error) {
                    runOnUiThread(() -> {
                        identifyBtn.setEnabled(true);
                        Toast.makeText(SpeciesActivity.this,
                                "Upload failed: " + error,
                                Toast.LENGTH_LONG).show();
                    });
                }
            });
        });
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

    private void showImageSourceDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Select Image Source");
        builder.setItems(new String[]{"Camera", "Gallery"}, (dialog, which) -> {
            if (which == 0) {
                takePhoto();
            } else {
                selectFromGallery();
            }
        });
        builder.show();
    }

    private void takePhoto() {
        Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        if (takePictureIntent.resolveActivity(getPackageManager()) != null) {
            File photoFile = null;
            try {
                photoFile = createImageFile();
            } catch (IOException ex) {
                Toast.makeText(this, "Error creating file", Toast.LENGTH_SHORT).show();
            }

            if (photoFile != null) {
                photoUri = FileProvider.getUriForFile(this,
                        "com.example.vitalarbor.fileprovider", photoFile);
                selectedFile = photoFile;
                takePictureIntent.putExtra(MediaStore.EXTRA_OUTPUT, photoUri);
                startActivityForResult(takePictureIntent, REQUEST_CAMERA);
            }
        }
    }

    private File createImageFile() throws IOException {
        String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
        String imageFileName = "SPECIES_" + timeStamp;
        File storageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        return File.createTempFile(imageFileName, ".jpg", storageDir);
    }

    private void selectFromGallery() {
        Intent intent = new Intent(Intent.ACTION_PICK, MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        startActivityForResult(intent, REQUEST_IMAGE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (resultCode == RESULT_OK) {
            if (requestCode == REQUEST_CAMERA) {
                // Image captured from camera
                if (selectedFile != null) {
                    displaySelectedImage();
                }
            } else if (requestCode == REQUEST_IMAGE && data != null) {
                // Image selected from gallery
                Uri selectedImageUri = data.getData();
                try {
                    String path = getPathFromUri(selectedImageUri);
                    if (path != null) {
                        selectedFile = new File(path);
                        displaySelectedImage();
                    }
                } catch (Exception e) {
                    Toast.makeText(this, "Error loading image", Toast.LENGTH_SHORT).show();
                }
            }
        }
    }

    private void displaySelectedImage() {
        if (selectedFile != null) {
            Bitmap bitmap = BitmapFactory.decodeFile(selectedFile.getAbsolutePath());
            selectedImageView.setImageBitmap(bitmap);
            selectedLabel.setText("✓ " + selectedFile.getName());
            selectedLabel.setTextColor(0xFF4CAF50); // Green
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
}