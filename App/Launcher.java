package App;

import javax.swing.*;
import java.awt.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;

public class Launcher {

    // Base URL of your VitalArbor backend API
    private static final String BASE_URL = "http://localhost:3000/api";
    
    // Debug mode flag
    private static boolean debugMode = false;
    
    // Debug console process
    private static Process debugConsoleProcess = null;
    
    // Get base directory for relative paths
    private static final File BASE_DIR = new File(System.getProperty("user.dir"));
    
    // Status label for displaying messages
    private static JLabel statusLabel;
    
    // Store credentials
    private static String currentUsername = null;
    private static String currentPassword = null;

    // Helper method to update status label
    private static void updateStatus(String message, Color color) {
        if (statusLabel != null) {
            SwingUtilities.invokeLater(() -> {
                statusLabel.setText(message);
                statusLabel.setForeground(color);
            });
        }
        System.out.println("[STATUS] " + message);
    }
    
    // Open a CMD window for debug output
    private static void openDebugConsole() {
        try {
            ProcessBuilder pb = new ProcessBuilder(
                "cmd.exe", 
                "/k", 
                "echo Debug Console - VitalArbor Launcher && echo. && echo Waiting for messages..."
            );
            pb.inheritIO();
            debugConsoleProcess = pb.start();
            System.out.println("[DEBUG] Debug console opened");
        } catch (Exception e) {
            System.err.println("[ERROR] Failed to open debug console: " + e.getMessage());
        }
    }
    
    // Close the debug console
    private static void closeDebugConsole() {
        if (debugConsoleProcess != null && debugConsoleProcess.isAlive()) {
            debugConsoleProcess.destroy();
            debugConsoleProcess = null;
            System.out.println("[DEBUG] Debug console closed");
        }
    }

    // Helper method: send POST request
    private static String sendPost(String endpoint, String jsonData) {
        try {
            URL url = new URL(BASE_URL + endpoint);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setRequestProperty("Accept", "application/json");
            conn.setDoOutput(true);
            conn.setConnectTimeout(10000);
            conn.setReadTimeout(10000);

            // Write the JSON data
            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = jsonData.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }

            // Read the response
            int status = conn.getResponseCode();
            InputStream is = (status < 400) ? conn.getInputStream() : conn.getErrorStream();

            try (BufferedReader br = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    response.append(line.trim());
                }
                
                // Debug output
                if (debugMode) {
                    System.out.println("[DEBUG] Request: " + endpoint);
                    System.out.println("[DEBUG] Body: " + jsonData);
                    System.out.println("[DEBUG] Status: " + status);
                    System.out.println("[DEBUG] Response: " + response.toString());
                }
                
                return response.toString();
            }
        } catch (Exception e) {
            updateStatus("Network error: " + e.getMessage(), Color.RED);
            if (debugMode) {
                e.printStackTrace();
            }
            return "{\"error\":\"Request failed: " + e.getMessage() + "\"}";
        }
    }

    // Custom rounded button
    static class RoundedButton extends JButton {
        private Color bgColor;
        
        public RoundedButton(String text, Color bgColor) {
            super(text);
            this.bgColor = bgColor;
            setContentAreaFilled(false);
            setBorderPainted(false);
            setFocusPainted(false);
            setForeground(Color.WHITE);
            setFont(new Font("Arial", Font.BOLD, 14));
        }
        
        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            
            if (getModel().isPressed()) {
                g2.setColor(bgColor.darker());
            } else if (getModel().isRollover()) {
                g2.setColor(bgColor.brighter());
            } else {
                g2.setColor(bgColor);
            }
            
            g2.fillRoundRect(0, 0, getWidth(), getHeight(), 25, 25);
            g2.dispose();
            
            super.paintComponent(g);
        }
    }

    // Custom rounded text field
    static class RoundedTextField extends JTextField {
        public RoundedTextField(int columns) {
            super(columns);
            setOpaque(false);
            setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));
        }
        
        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setColor(Color.WHITE);
            g2.fillRoundRect(0, 0, getWidth(), getHeight(), 15, 15);
            g2.dispose();
            super.paintComponent(g);
        }
        
        @Override
        protected void paintBorder(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setColor(new Color(200, 200, 200));
            g2.drawRoundRect(0, 0, getWidth()-1, getHeight()-1, 15, 15);
            g2.dispose();
        }
    }
    
    // Custom rounded password field
    static class RoundedPasswordField extends JPasswordField {
        public RoundedPasswordField(int columns) {
            super(columns);
            setOpaque(false);
            setBorder(BorderFactory.createEmptyBorder(10, 15, 10, 15));
        }
        
        @Override
        protected void paintComponent(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setColor(Color.WHITE);
            g2.fillRoundRect(0, 0, getWidth(), getHeight(), 15, 15);
            g2.dispose();
            super.paintComponent(g);
        }
        
        @Override
        protected void paintBorder(Graphics g) {
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2.setColor(new Color(200, 200, 200));
            g2.drawRoundRect(0, 0, getWidth()-1, getHeight()-1, 15, 15);
            g2.dispose();
        }
    }

    // Open Dashboard window
    private static void openDashboard(JFrame parentFrame, String username, String password) {
        parentFrame.dispose();
        
        JFrame dashboard = new JFrame("VitalArbor - Dashboard");
        dashboard.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        dashboard.setSize(900, 600);
        dashboard.setLayout(new BorderLayout());

        // Header panel
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(45, 80, 22));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(15, 20, 15, 20));
        
        JLabel titleLabel = new JLabel("🌲 VitalArbor");
        titleLabel.setFont(new Font("Arial", Font.BOLD, 24));
        titleLabel.setForeground(Color.WHITE);
        
        JLabel userLabel = new JLabel("Welcome, " + username + "!");
        userLabel.setFont(new Font("Arial", Font.PLAIN, 14));
        userLabel.setForeground(Color.WHITE);
        
        RoundedButton logoutBtn = new RoundedButton("Logout", new Color(200, 50, 50));
        logoutBtn.setPreferredSize(new Dimension(100, 35));
        logoutBtn.addActionListener(e -> {
            dashboard.dispose();
            main(null);
        });
        
        JPanel headerLeft = new JPanel(new BorderLayout());
        headerLeft.setOpaque(false);
        headerLeft.add(titleLabel, BorderLayout.NORTH);
        headerLeft.add(userLabel, BorderLayout.SOUTH);
        
        headerPanel.add(headerLeft, BorderLayout.WEST);
        headerPanel.add(logoutBtn, BorderLayout.EAST);

        // Main content
        JPanel contentPanel = new JPanel();
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setBorder(BorderFactory.createEmptyBorder(20, 30, 20, 30));
        contentPanel.setBackground(Color.WHITE);
        
        // Upload section
        JPanel uploadPanel = new JPanel();
        uploadPanel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(102, 255, 102), 2),
            "Upload Tree Image"
        ));
        uploadPanel.setLayout(new FlowLayout(FlowLayout.CENTER, 20, 20));
        uploadPanel.setBackground(Color.WHITE);
        
        RoundedButton uploadBtn = new RoundedButton("📤 Choose Image to Upload", new Color(102, 255, 102));
        uploadBtn.setPreferredSize(new Dimension(300, 50));
        uploadBtn.setFont(new Font("Arial", Font.BOLD, 16));
        
        JLabel uploadStatus = new JLabel("");
        uploadStatus.setFont(new Font("Arial", Font.PLAIN, 12));
        
        uploadBtn.addActionListener(e -> {
            JFileChooser fileChooser = new JFileChooser();
            fileChooser.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter(
                "Image files", "jpg", "jpeg", "png", "gif"
            ));
            
            int result = fileChooser.showOpenDialog(dashboard);
            if (result == JFileChooser.APPROVE_OPTION) {
                File selectedFile = fileChooser.getSelectedFile();
                uploadStatus.setText("Uploading " + selectedFile.getName() + "...");
                uploadStatus.setForeground(Color.BLUE);
                
                new Thread(() -> {
                    try {
                        boolean success = uploadImage(selectedFile, username, password);
                        SwingUtilities.invokeLater(() -> {
                            if (success) {
                                uploadStatus.setText("✓ Upload successful!");
                                uploadStatus.setForeground(new Color(0, 200, 0));
                            } else {
                                uploadStatus.setText("✗ Upload failed");
                                uploadStatus.setForeground(Color.RED);
                            }
                        });
                    } catch (Exception ex) {
                        SwingUtilities.invokeLater(() -> {
                            uploadStatus.setText("✗ Error: " + ex.getMessage());
                            uploadStatus.setForeground(Color.RED);
                        });
                    }
                }).start();
            }
        });
        
        uploadPanel.add(uploadBtn);
        uploadPanel.add(uploadStatus);

        // Images section
        JPanel imagesPanel = new JPanel(new BorderLayout());
        imagesPanel.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(new Color(102, 255, 102), 2),
            "Your Tree Images"
        ));
        imagesPanel.setBackground(Color.WHITE);
        
        RoundedButton loadImagesBtn = new RoundedButton("🔄 Load My Images", new Color(102, 255, 102));
        loadImagesBtn.setFont(new Font("Arial", Font.BOLD, 14));
        loadImagesBtn.setPreferredSize(new Dimension(150, 40));
        
        JTextArea imagesArea = new JTextArea(15, 60);
        imagesArea.setEditable(false);
        imagesArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        JScrollPane scrollPane = new JScrollPane(imagesArea);
        
        loadImagesBtn.addActionListener(e -> {
            imagesArea.setText("Loading images...\n");
            
            new Thread(() -> {
                String response = loadUserImages(username, password);
                SwingUtilities.invokeLater(() -> {
                    imagesArea.setText(response);
                });
            }).start();
        });
        
        JPanel btnPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        btnPanel.setBackground(Color.WHITE);
        btnPanel.add(loadImagesBtn);
        
        imagesPanel.add(btnPanel, BorderLayout.NORTH);
        imagesPanel.add(scrollPane, BorderLayout.CENTER);

        contentPanel.add(uploadPanel);
        contentPanel.add(Box.createVerticalStrut(20));
        contentPanel.add(imagesPanel);

        dashboard.add(headerPanel, BorderLayout.NORTH);
        dashboard.add(new JScrollPane(contentPanel), BorderLayout.CENTER);
        
        dashboard.setVisible(true);
    }
    
    // Upload image using multipart form data
    private static boolean uploadImage(File imageFile, String username, String password) {
        try {
            if (debugMode) {
                System.out.println("[DEBUG] ========== IMAGE UPLOAD START ==========");
                System.out.println("[DEBUG] File: " + imageFile.getAbsolutePath());
                System.out.println("[DEBUG] File exists: " + imageFile.exists());
                System.out.println("[DEBUG] File size: " + imageFile.length() + " bytes");
                System.out.println("[DEBUG] Username: " + username);
            }
            
            String boundary = "----VitalArborBoundary" + System.currentTimeMillis();
            URL url = new URL(BASE_URL + "/upload");
            
            if (debugMode) {
                System.out.println("[DEBUG] Upload URL: " + url);
                System.out.println("[DEBUG] Boundary: " + boundary);
            }
            
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setDoOutput(true);
            conn.setDoInput(true);
            conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
            conn.setConnectTimeout(30000);
            conn.setReadTimeout(30000);

            if (debugMode) {
                System.out.println("[DEBUG] Connection opened, writing multipart data...");
            }

            try (OutputStream os = conn.getOutputStream();
                 PrintWriter writer = new PrintWriter(new OutputStreamWriter(os, StandardCharsets.UTF_8), true)) {
                
                if (debugMode) System.out.println("[DEBUG] Writing username field...");
                writer.append("--").append(boundary).append("\r\n");
                writer.append("Content-Disposition: form-data; name=\"username\"\r\n\r\n");
                writer.append(username).append("\r\n");
                writer.flush();
                
                if (debugMode) System.out.println("[DEBUG] Writing password field...");
                writer.append("--").append(boundary).append("\r\n");
                writer.append("Content-Disposition: form-data; name=\"password\"\r\n\r\n");
                writer.append(password).append("\r\n");
                writer.flush();
                
                if (debugMode) System.out.println("[DEBUG] Writing image file...");
                writer.append("--").append(boundary).append("\r\n");
                writer.append("Content-Disposition: form-data; name=\"image\"; filename=\"")
                      .append(imageFile.getName()).append("\"\r\n");
                
                String contentType = "application/octet-stream";
                String fileName = imageFile.getName().toLowerCase();
                if (fileName.endsWith(".jpg") || fileName.endsWith(".jpeg")) {
                    contentType = "image/jpeg";
                } else if (fileName.endsWith(".png")) {
                    contentType = "image/png";
                } else if (fileName.endsWith(".gif")) {
                    contentType = "image/gif";
                }
                
                writer.append("Content-Type: ").append(contentType).append("\r\n");
                writer.append("Content-Transfer-Encoding: binary\r\n\r\n");
                writer.flush();
                
                if (debugMode) System.out.println("[DEBUG] Writing image bytes...");
                long bytesWritten = 0;
                try (FileInputStream fis = new FileInputStream(imageFile)) {
                    byte[] buffer = new byte[4096];
                    int bytesRead;
                    while ((bytesRead = fis.read(buffer)) != -1) {
                        os.write(buffer, 0, bytesRead);
                        bytesWritten += bytesRead;
                    }
                }
                os.flush();
                
                if (debugMode) {
                    System.out.println("[DEBUG] Image bytes written: " + bytesWritten);
                }
                
                writer.append("\r\n");
                writer.append("--").append(boundary).append("--\r\n");
                writer.flush();
                
                if (debugMode) System.out.println("[DEBUG] Multipart data complete, reading response...");
            }

            int status = conn.getResponseCode();
            String statusMessage = conn.getResponseMessage();
            
            if (debugMode) {
                System.out.println("[DEBUG] Response Status: " + status + " " + statusMessage);
            }
            
            InputStream is = (status < 400) ? conn.getInputStream() : conn.getErrorStream();
            StringBuilder response = new StringBuilder();
            
            try (BufferedReader br = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
                String line;
                while ((line = br.readLine()) != null) {
                    response.append(line);
                }
            }
            
            if (debugMode) {
                System.out.println("[DEBUG] Response Body: " + response.toString());
                System.out.println("[DEBUG] ========== IMAGE UPLOAD END ==========");
            }
            
            boolean success = status >= 200 && status < 300;
            
            if (!success) {
                System.err.println("[ERROR] Upload failed with status " + status + ": " + response.toString());
            }
            
            return success;
            
        } catch (Exception e) {
            System.err.println("[ERROR] Upload exception: " + e.getClass().getName() + " - " + e.getMessage());
            if (debugMode) {
                e.printStackTrace();
            }
            return false;
        }
    }

    // Load user's images
    private static String loadUserImages(String username, String password) {
        String json = String.format("{\"username\":\"%s\",\"password\":\"%s\"}", username, password);
        String response = sendPost("/images", json);
        
        try {
            if (response.contains("\"images\":[")) {
                if (response.contains("\"images\":[]")) {
                    return "No images found.\n\nUpload your first tree image to get started!";
                }
                
                int count = 0;
                int index = response.indexOf("\"url\":");
                while (index != -1) {
                    count++;
                    index = response.indexOf("\"url\":", index + 1);
                }
                
                return String.format("Found %d image(s) in your account!\n\nYour images are stored in Firebase Storage.\n\nResponse data:\n%s", count, response);
            } else if (response.contains("error")) {
                return "Error loading images:\n" + response;
            } else {
                return "Unexpected response:\n" + response;
            }
        } catch (Exception e) {
            return "Error parsing response:\n" + e.getMessage();
        }
    }

    public static void main(String[] args) {
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            closeDebugConsole();
        }));

        JFrame frame = new JFrame("VitalArbor");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(900, 650);
        frame.setLayout(new GridLayout(1, 2));
        
        // Load and set icon
        try {
            File logoFile = new File(BASE_DIR, "Logo.png");
            if (logoFile.exists()) {
                ImageIcon icon = new ImageIcon(logoFile.getAbsolutePath());
                frame.setIconImage(icon.getImage());
            }
        } catch (Exception e) {
            System.err.println("Could not load logo: " + e.getMessage());
        }

        // LEFT PANEL - Benefits with logo
        JPanel leftPanel = new JPanel();
        leftPanel.setBackground(new Color(135, 206, 235)); // Sky blue from image
        leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
        leftPanel.setBorder(BorderFactory.createEmptyBorder(40, 40, 40, 40));
        
        // Logo image
        try {
            File logoFile = new File(BASE_DIR, "Logo.png");
            if (logoFile.exists()) {
                ImageIcon logoIcon = new ImageIcon(logoFile.getAbsolutePath());
                Image scaledLogo = logoIcon.getImage().getScaledInstance(200, 200, Image.SCALE_SMOOTH);
                JLabel logoLabel = new JLabel(new ImageIcon(scaledLogo));
                logoLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
                leftPanel.add(logoLabel);
                leftPanel.add(Box.createVerticalStrut(30));
            }
        } catch (Exception e) {
            System.err.println("Could not load logo for left panel: " + e.getMessage());
        }
        
        JLabel benefitsTitle = new JLabel("Join VitalArbor and get access to:");
        benefitsTitle.setFont(new Font("SansSerif", Font.BOLD, 20));
        benefitsTitle.setForeground(new Color(45, 60, 30)); // Dark green from tree
        benefitsTitle.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        String[] benefits = {
            "• Instant tree health analysis",
            "• Quick tree problems detection",
            "• Smart tree care progress tracking",
            "• Personalized care planning & reminders",
            "• Customized tree collections"
        };
        
        leftPanel.add(benefitsTitle);
        leftPanel.add(Box.createVerticalStrut(25));
        
        for (String benefit : benefits) {
            JLabel benefitLabel = new JLabel(benefit);
            benefitLabel.setFont(new Font("SansSerif", Font.PLAIN, 15));
            benefitLabel.setForeground(new Color(60, 80, 40)); // Medium green
            benefitLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
            leftPanel.add(benefitLabel);
            leftPanel.add(Box.createVerticalStrut(12));
        }

        // RIGHT PANEL - Login Form
        JPanel rightPanel = new JPanel();
        rightPanel.setBackground(new Color(250, 245, 230)); // Warm sand/ground color from image
        rightPanel.setLayout(new BoxLayout(rightPanel, BoxLayout.Y_AXIS));
        rightPanel.setBorder(BorderFactory.createEmptyBorder(40, 50, 40, 50));
        
        // Title
        JLabel titleLabel = new JLabel("Sign In");
        titleLabel.setFont(new Font("SansSerif", Font.BOLD, 32));
        titleLabel.setForeground(new Color(45, 60, 30)); // Dark green
        titleLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        rightPanel.add(titleLabel);
        rightPanel.add(Box.createVerticalStrut(40));
        
        // Username field
        JLabel userLabel = new JLabel("Enter your username");
        userLabel.setFont(new Font("SansSerif", Font.PLAIN, 13));
        userLabel.setForeground(new Color(60, 80, 40));
        userLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        RoundedTextField userField = new RoundedTextField(20);
        userField.setMaximumSize(new Dimension(350, 45));
        userField.setFont(new Font("SansSerif", Font.PLAIN, 14));
        
        rightPanel.add(userLabel);
        rightPanel.add(Box.createVerticalStrut(8));
        rightPanel.add(userField);
        rightPanel.add(Box.createVerticalStrut(20));
        
        // Password field
        JLabel passLabel = new JLabel("Enter password");
        passLabel.setFont(new Font("SansSerif", Font.PLAIN, 13));
        passLabel.setForeground(new Color(60, 80, 40));
        passLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        RoundedPasswordField passField = new RoundedPasswordField(20);
        passField.setMaximumSize(new Dimension(350, 45));
        passField.setFont(new Font("SansSerif", Font.PLAIN, 14));
        
        rightPanel.add(passLabel);
        rightPanel.add(Box.createVerticalStrut(8));
        rightPanel.add(passField);
        rightPanel.add(Box.createVerticalStrut(30));
        
        // Sign In button - vibrant leaf green
        RoundedButton signInBtn = new RoundedButton("Sign In", new Color(139, 195, 74));
        signInBtn.setMaximumSize(new Dimension(350, 50));
        signInBtn.setAlignmentX(Component.CENTER_ALIGNMENT);
        signInBtn.setFont(new Font("SansSerif", Font.BOLD, 16));
        
        rightPanel.add(signInBtn);
        rightPanel.add(Box.createVerticalStrut(15));
        
        // Status label
        statusLabel = new JLabel("");
        statusLabel.setFont(new Font("SansSerif", Font.PLAIN, 12));
        statusLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        rightPanel.add(statusLabel);
        rightPanel.add(Box.createVerticalStrut(20));
        
        // Sign Up link - darker green
        JLabel signUpLabel = new JLabel("<html>Don't have an account? <font color='#8B6F47'><u>Sign Up</u></font></html>");
        signUpLabel.setFont(new Font("SansSerif", Font.PLAIN, 13));
        signUpLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        signUpLabel.setCursor(new Cursor(Cursor.HAND_CURSOR));
        signUpLabel.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseClicked(java.awt.event.MouseEvent evt) {
                showSignUpDialog(frame);
            }
        });
        
        rightPanel.add(signUpLabel);
        rightPanel.add(Box.createVerticalStrut(15));
        
        // Guest button - brown/trunk color
        RoundedButton guestBtn = new RoundedButton("Continue as Guest", new Color(139, 111, 71));
        guestBtn.setMaximumSize(new Dimension(200, 40));
        guestBtn.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        rightPanel.add(guestBtn);
        rightPanel.add(Box.createVerticalStrut(15));
        
        // Debug checkbox
        JCheckBox debugCheckBox = new JCheckBox("Debug Mode");
        debugCheckBox.setBackground(new Color(250, 245, 230));
        debugCheckBox.setForeground(new Color(60, 80, 40));
        debugCheckBox.setAlignmentX(Component.CENTER_ALIGNMENT);
        rightPanel.add(debugCheckBox);

        frame.add(leftPanel);
        frame.add(rightPanel);

        // Event handlers
        debugCheckBox.addActionListener(e -> {
            debugMode = debugCheckBox.isSelected();
            if (debugMode) {
                updateStatus("Debug mode enabled", new Color(139, 195, 74));
                openDebugConsole();
            } else {
                updateStatus("Debug mode disabled", Color.GRAY);
                closeDebugConsole();
            }
        });

        signInBtn.addActionListener(e -> {
            String username = userField.getText().trim();
            String password = new String(passField.getPassword());

            if (username.isEmpty() || password.isEmpty()) {
                updateStatus("Please enter username and password!", new Color(200, 80, 60));
                return;
            }

            updateStatus("Logging in...", new Color(60, 120, 180));
            String json = String.format("{\"username\":\"%s\",\"password\":\"%s\"}", username, password);
            String response = sendPost("/login", json);

            if (!response.contains("error")) {
                updateStatus("Login successful!", new Color(76, 175, 80));
                currentUsername = username;
                currentPassword = password;
                openDashboard(frame, username, password);
            } else {
                updateStatus("Login failed - check credentials or backend", new Color(200, 80, 60));
            }
        });

        guestBtn.addActionListener(e -> {
            updateStatus("Opening guest dashboard...", new Color(139, 195, 74));
            openDashboard(frame, "Guest", null);
        });

        frame.setVisible(true);
    }
    
    private static void showSignUpDialog(JFrame parent) {
        JDialog dialog = new JDialog(parent, "Sign Up", true);
        dialog.setSize(400, 350);
        dialog.setLocationRelativeTo(parent);
        dialog.setLayout(new BorderLayout());
        
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBorder(BorderFactory.createEmptyBorder(30, 40, 30, 40));
        panel.setBackground(new Color(250, 245, 230));
        
        JLabel title = new JLabel("Create Account");
        title.setFont(new Font("SansSerif", Font.BOLD, 24));
        title.setForeground(new Color(45, 60, 30));
        title.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        RoundedTextField usernameField = new RoundedTextField(20);
        usernameField.setMaximumSize(new Dimension(300, 40));
        
        RoundedPasswordField passwordField = new RoundedPasswordField(20);
        passwordField.setMaximumSize(new Dimension(300, 40));
        
        RoundedButton signUpBtn = new RoundedButton("Sign Up", new Color(139, 195, 74));
        signUpBtn.setMaximumSize(new Dimension(300, 45));
        
        JLabel userLbl = new JLabel("Username:");
        userLbl.setForeground(new Color(60, 80, 40));
        userLbl.setFont(new Font("SansSerif", Font.PLAIN, 13));
        
        JLabel passLbl = new JLabel("Password:");
        passLbl.setForeground(new Color(60, 80, 40));
        passLbl.setFont(new Font("SansSerif", Font.PLAIN, 13));
        
        panel.add(title);
        panel.add(Box.createVerticalStrut(30));
        panel.add(userLbl);
        panel.add(Box.createVerticalStrut(5));
        panel.add(usernameField);
        panel.add(Box.createVerticalStrut(15));
        panel.add(passLbl);
        panel.add(Box.createVerticalStrut(5));
        panel.add(passwordField);
        panel.add(Box.createVerticalStrut(25));
        panel.add(signUpBtn);
        
        signUpBtn.addActionListener(e -> {
            String username = usernameField.getText().trim();
            String password = new String(passwordField.getPassword());
            
            if (username.isEmpty() || password.isEmpty()) {
                JOptionPane.showMessageDialog(dialog, "Please fill all fields!");
                return;
            }
            
            if (password.length() < 6) {
                JOptionPane.showMessageDialog(dialog, "Password must be at least 6 characters!");
                return;
            }
            
            String json = String.format("{\"username\":\"%s\",\"password\":\"%s\"}", username, password);
            String response = sendPost("/signup", json);
            
            if (!response.contains("error")) {
                JOptionPane.showMessageDialog(dialog, "Account created! You can now login.");
                dialog.dispose();
            } else if (response.contains("already exists")) {
                JOptionPane.showMessageDialog(dialog, "Username already taken!");
            } else {
                JOptionPane.showMessageDialog(dialog, "Error creating account!");
            }
        });
        
        dialog.add(panel);
        dialog.setVisible(true);
    }
}