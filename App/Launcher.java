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
    
    // Get base directory for relative paths - should be the App folder
    private static final File BASE_DIR = new File(System.getProperty("user.dir"), "App");
    
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

    // Run Python pipeline
    private static String runPythonPipeline(String classificationPath, String tiltPath, String backupPath, 
                                            boolean useCutout, int detectionMethod) {
        try {
            // Build path to Python script - go up one level, then into Pipelines folder
            File pythonScript = new File(BASE_DIR.getParentFile(), "Pipelines/pipeline_runner.py");
            
            if (!pythonScript.exists()) {
                return "ERROR: Python pipeline not found at: " + pythonScript.getAbsolutePath();
            }
            
            if (debugMode) {
                System.out.println("[DEBUG] Running Python pipeline...");
                System.out.println("[DEBUG] Script: " + pythonScript.getAbsolutePath());
                System.out.println("[DEBUG] Classification photo: " + classificationPath);
                System.out.println("[DEBUG] Tilt photo: " + tiltPath);
                System.out.println("[DEBUG] Backup photo: " + backupPath);
                System.out.println("[DEBUG] Use cutout: " + useCutout);
                System.out.println("[DEBUG] Detection method: " + detectionMethod);
            }
            
            // Build command with arguments - use python -u for unbuffered output
            ProcessBuilder pb = new ProcessBuilder(
                "python",
                "-u",  // Unbuffered output - CRITICAL for real-time output
                pythonScript.getAbsolutePath(),
                classificationPath,
                tiltPath,
                backupPath,
                useCutout ? "y" : "n",
                String.valueOf(detectionMethod)
            );
            
            // Set working directory to Pipelines folder
            pb.directory(pythonScript.getParentFile());
            
            // Redirect error stream to output stream
            pb.redirectErrorStream(true);
            
            // Set environment to force Python unbuffered mode
            pb.environment().put("PYTHONUNBUFFERED", "1");
            
            if (debugMode) {
                System.out.println("[DEBUG] Starting Python process...");
                System.out.println("[DEBUG] Working directory: " + pythonScript.getParentFile());
                System.out.println("[DEBUG] Command: " + String.join(" ", pb.command()));
            }
            
            // Start process
            Process process = pb.start();
            
            // Read output in real-time with explicit flushing
            StringBuilder output = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                System.out.println("[PYTHON] Starting to read output...");
                while ((line = reader.readLine()) != null) {
                    output.append(line).append("\n");
                    System.out.println("[PYTHON] " + line);
                    System.out.flush(); // Force console output
                    
                    if (debugMode) {
                        System.out.println("[DEBUG] Python output: " + line);
                    }
                }
                System.out.println("[PYTHON] Finished reading output.");
            }
            
            // Wait for completion with timeout
            boolean finished = process.waitFor(300, java.util.concurrent.TimeUnit.SECONDS);
            
            if (!finished) {
                process.destroy();
                return "ERROR: Pipeline timed out after 5 minutes";
            }
            
            int exitCode = process.exitValue();
            
            if (debugMode) {
                System.out.println("[DEBUG] Python pipeline exit code: " + exitCode);
                System.out.println("[DEBUG] Output length: " + output.length() + " characters");
            }
            
            String outputStr = output.toString();
            
            if (outputStr.trim().isEmpty()) {
                return "ERROR: Python script produced no output. Exit code: " + exitCode + 
                       "\n\nPossible causes:\n" +
                       "- Script is waiting for user input\n" +
                       "- Script has syntax errors\n" +
                       "- Python path is incorrect\n\n" +
                       "Try running the script manually:\n" +
                       "python \"" + pythonScript.getAbsolutePath() + "\" \"" + 
                       classificationPath + "\" \"" + tiltPath + "\" \"" + backupPath + "\" " +
                       (useCutout ? "y" : "n") + " " + detectionMethod;
            }
            
            if (exitCode == 0) {
                return outputStr;
            } else {
                return "ERROR: Pipeline failed with exit code " + exitCode + "\n\nOutput:\n" + outputStr;
            }
            
        } catch (Exception e) {
            String errorMsg = "ERROR running Python pipeline: " + e.getMessage();
            if (debugMode) {
                e.printStackTrace();
            }
            return errorMsg;
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
        dashboard.setSize(1100, 700);
        dashboard.setLayout(new BorderLayout());
        
        // Set icon
        try {
            File logoFile = new File(BASE_DIR, "Logo.png");
            if (logoFile.exists()) {
                ImageIcon icon = new ImageIcon(logoFile.getAbsolutePath());
                dashboard.setIconImage(icon.getImage());
            }
        } catch (Exception e) {
            System.err.println("Could not load logo for dashboard: " + e.getMessage());
        }

        // Top Header Bar
        JPanel headerPanel = new JPanel(new BorderLayout());
        headerPanel.setBackground(new Color(45, 60, 30));
        headerPanel.setBorder(BorderFactory.createEmptyBorder(15, 25, 15, 25));
        
        JLabel titleLabel = new JLabel("🌲 VitalArbor");
        titleLabel.setFont(new Font("SansSerif", Font.BOLD, 26));
        titleLabel.setForeground(Color.WHITE);
        
        JLabel userLabel = new JLabel("Welcome, " + username + "!");
        userLabel.setFont(new Font("SansSerif", Font.PLAIN, 14));
        userLabel.setForeground(new Color(200, 220, 180));
        
        RoundedButton logoutBtn = new RoundedButton("Logout", new Color(200, 80, 60));
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

        // Main Content Area
        JPanel contentPanel = new JPanel(new BorderLayout());
        contentPanel.setBackground(new Color(250, 245, 230));
        
        // Center content with cards
        JPanel centerPanel = new JPanel();
        centerPanel.setLayout(new BoxLayout(centerPanel, BoxLayout.Y_AXIS));
        centerPanel.setBackground(new Color(250, 245, 230));
        centerPanel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        
        // Welcome card
        JPanel welcomeCard = createCard("Welcome to VitalArbor!", 
            "Manage your trees, get health diagnoses, and identify species.", 
            new Color(135, 206, 235));
        centerPanel.add(welcomeCard);
        centerPanel.add(Box.createVerticalStrut(15));
        
        // Quick stats card
        JPanel statsCard = createStatsCard(username);
        centerPanel.add(statsCard);
        
        contentPanel.add(new JScrollPane(centerPanel), BorderLayout.CENTER);

        // Bottom Navigation Bar
        JPanel bottomNav = new JPanel(new GridLayout(1, 3, 2, 0));
        bottomNav.setBackground(new Color(45, 60, 30));
        bottomNav.setBorder(BorderFactory.createEmptyBorder(0, 0, 0, 0));
        
        // Diagnosis Tab
        JPanel diagnosisTab = createNavTab("🔬 Get Diagnosis", "Upload or capture tree images", e -> {
            showDiagnosisPanel(dashboard, username, password);
        });
        
        // My Trees Tab
        JPanel treesTab = createNavTab("🌳 My Trees", "View your tree collection", e -> {
            showMyTreesPanel(dashboard, username, password);
        });
        
        // Species Detection Tab
        JPanel speciesTab = createNavTab("🔍 Identify Species", "Detect tree species from photo", e -> {
            showSpeciesPanel(dashboard, username, password);
        });
        
        bottomNav.add(diagnosisTab);
        bottomNav.add(treesTab);
        bottomNav.add(speciesTab);

        dashboard.add(headerPanel, BorderLayout.NORTH);
        dashboard.add(contentPanel, BorderLayout.CENTER);
        dashboard.add(bottomNav, BorderLayout.SOUTH);
        
        dashboard.setVisible(true);
    }
    
    // Create a modern card panel
    private static JPanel createCard(String title, String description, Color accentColor) {
        JPanel card = new JPanel();
        card.setLayout(new BoxLayout(card, BoxLayout.Y_AXIS));
        card.setBackground(Color.WHITE);
        card.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(200, 200, 200), 1),
            BorderFactory.createEmptyBorder(20, 25, 20, 25)
        ));
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 120));
        
        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("SansSerif", Font.BOLD, 20));
        titleLabel.setForeground(new Color(45, 60, 30));
        titleLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel descLabel = new JLabel(description);
        descLabel.setFont(new Font("SansSerif", Font.PLAIN, 14));
        descLabel.setForeground(new Color(100, 100, 100));
        descLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        card.add(titleLabel);
        card.add(Box.createVerticalStrut(8));
        card.add(descLabel);
        
        return card;
    }
    
    // Create stats card
    private static JPanel createStatsCard(String username) {
        JPanel card = new JPanel(new GridLayout(1, 3, 15, 0));
        card.setBackground(Color.WHITE);
        card.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(new Color(200, 200, 200), 1),
            BorderFactory.createEmptyBorder(25, 25, 25, 25)
        ));
        card.setMaximumSize(new Dimension(Integer.MAX_VALUE, 120));
        
        card.add(createStatItem("0", "Trees Monitored", new Color(76, 175, 80)));
        card.add(createStatItem("0", "Diagnoses", new Color(139, 195, 74)));
        card.add(createStatItem("0", "Species Identified", new Color(135, 206, 235)));
        
        return card;
    }
    
    private static JPanel createStatItem(String value, String label, Color color) {
        JPanel item = new JPanel();
        item.setLayout(new BoxLayout(item, BoxLayout.Y_AXIS));
        item.setBackground(Color.WHITE);
        
        JLabel valueLabel = new JLabel(value);
        valueLabel.setFont(new Font("SansSerif", Font.BOLD, 32));
        valueLabel.setForeground(color);
        valueLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel textLabel = new JLabel(label);
        textLabel.setFont(new Font("SansSerif", Font.PLAIN, 13));
        textLabel.setForeground(new Color(100, 100, 100));
        textLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        item.add(valueLabel);
        item.add(Box.createVerticalStrut(5));
        item.add(textLabel);
        
        return item;
    }
    
    // Create navigation tab
    private static JPanel createNavTab(String title, String subtitle, java.awt.event.ActionListener action) {
        JPanel tab = new JPanel();
        tab.setLayout(new BoxLayout(tab, BoxLayout.Y_AXIS));
        tab.setBackground(new Color(60, 80, 40));
        tab.setBorder(BorderFactory.createEmptyBorder(15, 10, 15, 10));
        tab.setCursor(new Cursor(Cursor.HAND_CURSOR));
        
        JLabel titleLabel = new JLabel(title);
        titleLabel.setFont(new Font("SansSerif", Font.BOLD, 16));
        titleLabel.setForeground(Color.WHITE);
        titleLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel subtitleLabel = new JLabel(subtitle);
        subtitleLabel.setFont(new Font("SansSerif", Font.PLAIN, 11));
        subtitleLabel.setForeground(new Color(200, 220, 180));
        subtitleLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        tab.add(titleLabel);
        tab.add(Box.createVerticalStrut(5));
        tab.add(subtitleLabel);
        
        // Hover effect
        tab.addMouseListener(new java.awt.event.MouseAdapter() {
            public void mouseEntered(java.awt.event.MouseEvent evt) {
                tab.setBackground(new Color(76, 100, 50));
            }
            public void mouseExited(java.awt.event.MouseEvent evt) {
                tab.setBackground(new Color(60, 80, 40));
            }
            public void mouseClicked(java.awt.event.MouseEvent evt) {
                if (action != null) {
                    action.actionPerformed(null);
                }
            }
        });
        
        return tab;
    }
    
    // Show Diagnosis Panel with Python Pipeline Integration
    private static void showDiagnosisPanel(JFrame dashboard, String username, String password) {
        JDialog dialog = new JDialog(dashboard, "Get Tree Diagnosis", true);
        dialog.setSize(700, 750);
        dialog.setLocationRelativeTo(dashboard);
        
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(new Color(250, 245, 230));
        panel.setBorder(BorderFactory.createEmptyBorder(30, 40, 30, 40));
        
        JLabel title = new JLabel("Upload Tree Images for Diagnosis");
        title.setFont(new Font("SansSerif", Font.BOLD, 22));
        title.setForeground(new Color(45, 60, 30));
        title.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel instruction = new JLabel("Upload 3 images of your tree from different angles");
        instruction.setFont(new Font("SansSerif", Font.PLAIN, 14));
        instruction.setForeground(new Color(100, 100, 100));
        instruction.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel[] imageLabels = new JLabel[3];
        File[] selectedFiles = new File[3];
        String[] imageTypes = {"Tree Classification", "Tilt Detection", "Trunk to Ground"};
        
        JPanel imagesGrid = new JPanel(new GridLayout(1, 3, 15, 0));
        imagesGrid.setBackground(new Color(250, 245, 230));
        imagesGrid.setMaximumSize(new Dimension(650, 180));
        
        for (int i = 0; i < 3; i++) {
            int index = i;
            JPanel imageBox = new JPanel();
            imageBox.setLayout(new BoxLayout(imageBox, BoxLayout.Y_AXIS));
            imageBox.setBackground(Color.WHITE);
            imageBox.setBorder(BorderFactory.createLineBorder(new Color(200, 200, 200), 2));
            imageBox.setCursor(new Cursor(Cursor.HAND_CURSOR));
            
            imageLabels[i] = new JLabel("<html><center>" + imageTypes[i] + "<br>Click to select</center></html>");
            imageLabels[i].setFont(new Font("SansSerif", Font.PLAIN, 12));
            imageLabels[i].setForeground(new Color(150, 150, 150));
            imageLabels[i].setHorizontalAlignment(SwingConstants.CENTER);
            imageLabels[i].setAlignmentX(Component.CENTER_ALIGNMENT);
            
            imageBox.add(Box.createVerticalGlue());
            imageBox.add(imageLabels[i]);
            imageBox.add(Box.createVerticalGlue());
            
            imageBox.addMouseListener(new java.awt.event.MouseAdapter() {
                public void mouseClicked(java.awt.event.MouseEvent evt) {
                    JFileChooser fc = new JFileChooser();
                    fc.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter(
                        "Images", "jpg", "jpeg", "png", "gif"));
                    if (fc.showOpenDialog(dialog) == JFileChooser.APPROVE_OPTION) {
                        selectedFiles[index] = fc.getSelectedFile();
                        imageLabels[index].setText("<html><center>✓ " + imageTypes[index] + "<br>" + 
                            fc.getSelectedFile().getName() + "</center></html>");
                        imageLabels[index].setForeground(new Color(76, 175, 80));
                    }
                }
            });
            
            imagesGrid.add(imageBox);
        }
        
        // Options panel
        JPanel optionsPanel = new JPanel();
        optionsPanel.setLayout(new BoxLayout(optionsPanel, BoxLayout.Y_AXIS));
        optionsPanel.setBackground(new Color(250, 245, 230));
        optionsPanel.setMaximumSize(new Dimension(650, 120));
        optionsPanel.setBorder(BorderFactory.createEmptyBorder(10, 0, 10, 0));
        
        // Use cutout checkbox
        JCheckBox useCutoutCheck = new JCheckBox("Use trunk cutout for analysis");
        useCutoutCheck.setBackground(new Color(250, 245, 230));
        useCutoutCheck.setFont(new Font("SansSerif", Font.PLAIN, 13));
        useCutoutCheck.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        // Detection method selection
        JLabel methodLabel = new JLabel("Tilt Detection Method:");
        methodLabel.setFont(new Font("SansSerif", Font.BOLD, 13));
        methodLabel.setForeground(new Color(45, 60, 30));
        methodLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        String[] methods = {"Original (Line Intersection)", "PCA Method", "Combined (PCA + Lines)"};
        JComboBox<String> methodCombo = new JComboBox<>(methods);
        methodCombo.setMaximumSize(new Dimension(300, 35));
        methodCombo.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        optionsPanel.add(useCutoutCheck);
        optionsPanel.add(Box.createVerticalStrut(10));
        optionsPanel.add(methodLabel);
        optionsPanel.add(Box.createVerticalStrut(5));
        optionsPanel.add(methodCombo);
        
        // Diagnose button
        RoundedButton diagnoseBtn = new RoundedButton("Start Diagnosis", new Color(139, 195, 74));
        diagnoseBtn.setMaximumSize(new Dimension(200, 45));
        diagnoseBtn.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        // Progress label
        JLabel progressLabel = new JLabel("");
        progressLabel.setFont(new Font("SansSerif", Font.ITALIC, 12));
        progressLabel.setForeground(new Color(100, 100, 100));
        progressLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        diagnoseBtn.addActionListener(e -> {
            // Validate inputs
            int uploadedCount = 0;
            for (File f : selectedFiles) {
                if (f != null) uploadedCount++;
            }
            
            if (uploadedCount < 3) {
                JOptionPane.showMessageDialog(dialog, "Please select all 3 images!");
                return;
            }
            
            // Disable button and show progress
            diagnoseBtn.setEnabled(false);
            progressLabel.setText("Running analysis pipeline...");
            progressLabel.setForeground(new Color(139, 195, 74));
            
            // Run pipeline in background thread
            new Thread(() -> {
                try {
                    // Get parameters
                    String classificationPath = selectedFiles[0].getAbsolutePath();
                    String tiltPath = selectedFiles[1].getAbsolutePath();
                    String backupPath = selectedFiles[2].getAbsolutePath();
                    boolean useCutout = useCutoutCheck.isSelected();
                    int detectionMethod = methodCombo.getSelectedIndex() + 1; // 1, 2, or 3
                    
                    // Run pipeline
                    String result = runPythonPipeline(classificationPath, tiltPath, backupPath, 
                                                     useCutout, detectionMethod);
                    
                    // Show results on UI thread
                    SwingUtilities.invokeLater(() -> {
                        diagnoseBtn.setEnabled(true);
                        progressLabel.setText("");
                        
                        if (result.startsWith("ERROR")) {
                            JOptionPane.showMessageDialog(dialog, result, "Pipeline Error", 
                                                         JOptionPane.ERROR_MESSAGE);
                        } else {
                            // Show results in a dialog with the classification image
                            showResultsDialog(dialog, result, classificationPath);
                            dialog.dispose();
                        }
                    });
                    
                } catch (Exception ex) {
                    SwingUtilities.invokeLater(() -> {
                        diagnoseBtn.setEnabled(true);
                        progressLabel.setText("");
                        JOptionPane.showMessageDialog(dialog, 
                            "Error: " + ex.getMessage(), 
                            "Pipeline Error", 
                            JOptionPane.ERROR_MESSAGE);
                    });
                }
            }).start();
        });
        
        panel.add(title);
        panel.add(Box.createVerticalStrut(10));
        panel.add(instruction);
        panel.add(Box.createVerticalStrut(30));
        panel.add(imagesGrid);
        panel.add(Box.createVerticalStrut(20));
        panel.add(optionsPanel);
        panel.add(Box.createVerticalStrut(20));
        panel.add(diagnoseBtn);
        panel.add(Box.createVerticalStrut(10));
        panel.add(progressLabel);
        
        dialog.add(panel);
        dialog.setVisible(true);
    }
    
    // Custom panel with rounded corners for images
    static class RoundedImagePanel extends JPanel {
        private Image image;
        private int cornerRadius = 25;
        
        public RoundedImagePanel(Image img) {
            this.image = img;
            setOpaque(false);
        }
        
        @Override
        protected void paintComponent(Graphics g) {
            super.paintComponent(g);
            Graphics2D g2 = (Graphics2D) g.create();
            g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            
            if (image != null) {
                // Create rounded clipping area
                g2.setClip(new java.awt.geom.RoundRectangle2D.Float(0, 0, getWidth(), getHeight(), 
                           cornerRadius, cornerRadius));
                g2.drawImage(image, 0, 0, getWidth(), getHeight(), this);
            }
            
            g2.dispose();
        }
    }
    
    // Parse pipeline results and extract key information
    private static String[] parsePipelineResults(String results) {
        String riskScore = "N/A";
        String riskCategory = "Unknown";
        String tiltAngle = "N/A";
        String species = "N/A";
        String diagnosis = "N/A";
        String fixes = "N/A";
        
        // Parse risk score (looking for "Risk Score: XX.X")
        if (results.contains("Risk Score:")) {
            int start = results.indexOf("Risk Score:") + 11;
            int end = start;
            // Find the end of the number (could be space, newline, or /)
            while (end < results.length() && 
                   (Character.isDigit(results.charAt(end)) || results.charAt(end) == '.' || results.charAt(end) == ' ')) {
                if (results.charAt(end) == ' ' && end > start) break;
                if (Character.isDigit(results.charAt(end)) || results.charAt(end) == '.') {
                    end++;
                } else {
                    break;
                }
            }
            riskScore = results.substring(start, end).trim();
            // Also look for the format "Risk Score: XX.X / 40"
            int slashIndex = results.indexOf("/", start);
            if (slashIndex > start && slashIndex < start + 20) {
                riskScore = results.substring(start, slashIndex).trim();
            }
        }
        
        // Parse risk category (looking for "Category: HIGH RISK" or "Risk Category: ('HIGH RISK', 'orange')")
        if (results.contains("Category:")) {
            int categoryIndex = results.indexOf("Category:");
            int start = categoryIndex + 9;
            int end = results.indexOf("\n", start);
            if (end == -1) end = results.length();
            String categoryLine = results.substring(start, end).trim();
            
            // Handle tuple format: ('HIGH RISK', 'orange')
            if (categoryLine.contains("'")) {
                int firstQuote = categoryLine.indexOf("'");
                int secondQuote = categoryLine.indexOf("'", firstQuote + 1);
                if (secondQuote > firstQuote) {
                    riskCategory = categoryLine.substring(firstQuote + 1, secondQuote).trim();
                }
            } else {
                riskCategory = categoryLine.trim();
            }
        }
        
        // Parse tilt angle (looking for "Tilt Angle: XX.XX° from vertical" or "tilt angle: XX.XX°")
        if (results.contains("Tilt Angle:")) {
            int start = results.indexOf("Tilt Angle:") + 11;
            int end = results.indexOf("°", start);
            if (end != -1) {
                tiltAngle = results.substring(start, end).trim() + "°";
            }
        }
        
        // Parse species (looking for "Species: Prunus × yedoensis")
        if (results.contains("Species:")) {
            int start = results.indexOf("Species:") + 8;
            int end = results.indexOf("\n", start);
            if (end == -1) end = results.length();
            species = results.substring(start, end).trim();
        }
        
        // Parse diagnosis (looking for "Diagnosis of tree:")
        if (results.contains("Diagnosis of tree:")) {
            int start = results.indexOf("Diagnosis of tree:") + 18;
            int end = results.indexOf("Fixes/reccomendations:", start);
            if (end == -1) end = results.indexOf("## 1. IMMEDIATE SAFETY CONCERNS", start);
            if (end == -1) end = results.length();
            diagnosis = results.substring(start, end).trim();
        }
        
        // Parse fixes (looking for "Fixes/reccomendations:" or starting from "## 1. IMMEDIATE SAFETY CONCERNS")
        if (results.contains("Fixes/reccomendations:")) {
            int start = results.indexOf("Fixes/reccomendations:") + 22;
            int end = results.indexOf("============================================================", start);
            if (end == -1) end = results.indexOf("=== Analysis Complete ===", start);
            if (end == -1) end = results.length();
            fixes = results.substring(start, end).trim();
        } else if (results.contains("## 1. IMMEDIATE SAFETY CONCERNS")) {
            int start = results.indexOf("## 1. IMMEDIATE SAFETY CONCERNS");
            int end = results.indexOf("============================================================", start);
            if (end == -1) end = results.indexOf("=== Analysis Complete ===", start);
            if (end == -1) end = results.length();
            fixes = results.substring(start, end).trim();
        }
        
        return new String[]{riskScore, riskCategory, tiltAngle, species, diagnosis, fixes};
    }
    
    // Show results dialog with image and color-coded diagnosis
    private static void showResultsDialog(JDialog parent, String results, String imagePath) {
        JDialog resultsDialog = new JDialog(parent, "Tree Diagnosis Results", true);
        resultsDialog.setSize(900, 700);
        resultsDialog.setLocationRelativeTo(parent);
        
        JPanel mainPanel = new JPanel(new BorderLayout(20, 20));
        mainPanel.setBackground(new Color(250, 245, 230));
        mainPanel.setBorder(BorderFactory.createEmptyBorder(30, 30, 30, 30));
        
        // Title
        JLabel title = new JLabel("🌲 Tree Health Analysis Complete");
        title.setFont(new Font("SansSerif", Font.BOLD, 26));
        title.setForeground(new Color(45, 60, 30));
        title.setHorizontalAlignment(SwingConstants.CENTER);
        
        // Parse results
        String[] parsedData = parsePipelineResults(results);
        String riskScore = parsedData[0];
        String riskCategory = parsedData[1];
        String tiltAngle = parsedData[2];
        String species = parsedData[3];
        String diagnosis = parsedData[4];
        String fixes = parsedData[5];
        
        // Determine color based on risk category
        Color diagnosisColor;
        String riskCategoryLower = riskCategory.toLowerCase();
        if (riskCategoryLower.contains("low") || riskCategoryLower.contains("healthy")) {
            diagnosisColor = new Color(76, 175, 80); // Green
        } else if (riskCategoryLower.contains("medium") || riskCategoryLower.contains("moderate")) {
            diagnosisColor = new Color(255, 193, 7); // Yellow/Orange
        } else if (riskCategoryLower.contains("high") || riskCategoryLower.contains("orange")) {
            diagnosisColor = new Color(255, 152, 0); // Orange
        } else if (riskCategoryLower.contains("critical") || riskCategoryLower.contains("red")) {
            diagnosisColor = new Color(244, 67, 54); // Red
        } else {
            diagnosisColor = new Color(158, 158, 158); // Gray for unknown
        }
        
        // Content panel (holds image and diagnosis side by side)
        JPanel contentPanel = new JPanel(new GridLayout(1, 2, 20, 0));
        contentPanel.setBackground(new Color(250, 245, 230));
        
        // LEFT SIDE - Image with rounded corners
        JPanel imageContainer = new JPanel(new BorderLayout());
        imageContainer.setBackground(new Color(250, 245, 230));
        
        try {
            ImageIcon originalIcon = new ImageIcon(imagePath);
            Image scaledImage = originalIcon.getImage().getScaledInstance(400, 400, Image.SCALE_SMOOTH);
            RoundedImagePanel imagePanel = new RoundedImagePanel(scaledImage);
            imagePanel.setPreferredSize(new Dimension(400, 400));
            imageContainer.add(imagePanel, BorderLayout.CENTER);
        } catch (Exception e) {
            JLabel noImageLabel = new JLabel("Image not available");
            noImageLabel.setHorizontalAlignment(SwingConstants.CENTER);
            noImageLabel.setFont(new Font("SansSerif", Font.ITALIC, 14));
            imageContainer.add(noImageLabel, BorderLayout.CENTER);
        }
        
        // RIGHT SIDE - Diagnosis information
        JPanel diagnosisPanel = new JPanel();
        diagnosisPanel.setLayout(new BoxLayout(diagnosisPanel, BoxLayout.Y_AXIS));
        diagnosisPanel.setBackground(diagnosisColor);
        diagnosisPanel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(diagnosisColor.darker(), 3),
            BorderFactory.createEmptyBorder(20, 20, 20, 20)
        ));
        
        // Risk Category Header
        JLabel riskLabel = new JLabel("Risk Level: " + riskCategory);
        riskLabel.setFont(new Font("SansSerif", Font.BOLD, 22));
        riskLabel.setForeground(Color.WHITE);
        riskLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel scoreLabel = new JLabel("Score: " + riskScore);
        scoreLabel.setFont(new Font("SansSerif", Font.BOLD, 18));
        scoreLabel.setForeground(Color.WHITE);
        scoreLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Separator
        JSeparator separator = new JSeparator();
        separator.setForeground(Color.WHITE);
        separator.setMaximumSize(new Dimension(Integer.MAX_VALUE, 2));
        
        // Details
        JLabel speciesLabel = new JLabel("Species: " + species);
        speciesLabel.setFont(new Font("SansSerif", Font.PLAIN, 14));
        speciesLabel.setForeground(Color.WHITE);
        speciesLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel tiltLabel = new JLabel("Tilt: " + tiltAngle);
        tiltLabel.setFont(new Font("SansSerif", Font.PLAIN, 14));
        tiltLabel.setForeground(Color.WHITE);
        tiltLabel.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel diagnosisTitle = new JLabel("Diagnosis:");
        diagnosisTitle.setFont(new Font("SansSerif", Font.BOLD, 16));
        diagnosisTitle.setForeground(Color.WHITE);
        diagnosisTitle.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JTextArea diagnosisText = new JTextArea(diagnosis);
        diagnosisText.setFont(new Font("SansSerif", Font.PLAIN, 13));
        diagnosisText.setForeground(Color.WHITE);
        diagnosisText.setBackground(diagnosisColor);
        diagnosisText.setLineWrap(true);
        diagnosisText.setWrapStyleWord(true);
        diagnosisText.setEditable(false);
        diagnosisText.setOpaque(true);
        diagnosisText.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JLabel fixesTitle = new JLabel("Recommended Actions:");
        fixesTitle.setFont(new Font("SansSerif", Font.BOLD, 16));
        fixesTitle.setForeground(Color.WHITE);
        fixesTitle.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        JTextArea fixesText = new JTextArea(fixes);
        fixesText.setFont(new Font("SansSerif", Font.PLAIN, 13));
        fixesText.setForeground(Color.WHITE);
        fixesText.setBackground(diagnosisColor);
        fixesText.setLineWrap(true);
        fixesText.setWrapStyleWord(true);
        fixesText.setEditable(false);
        fixesText.setOpaque(true);
        fixesText.setAlignmentX(Component.LEFT_ALIGNMENT);
        
        // Add all components to diagnosis panel
        diagnosisPanel.add(riskLabel);
        diagnosisPanel.add(Box.createVerticalStrut(5));
        diagnosisPanel.add(scoreLabel);
        diagnosisPanel.add(Box.createVerticalStrut(15));
        diagnosisPanel.add(separator);
        diagnosisPanel.add(Box.createVerticalStrut(15));
        diagnosisPanel.add(speciesLabel);
        diagnosisPanel.add(Box.createVerticalStrut(5));
        diagnosisPanel.add(tiltLabel);
        diagnosisPanel.add(Box.createVerticalStrut(15));
        diagnosisPanel.add(diagnosisTitle);
        diagnosisPanel.add(Box.createVerticalStrut(5));
        diagnosisPanel.add(diagnosisText);
        diagnosisPanel.add(Box.createVerticalStrut(15));
        diagnosisPanel.add(fixesTitle);
        diagnosisPanel.add(Box.createVerticalStrut(5));
        diagnosisPanel.add(fixesText);
        
        contentPanel.add(imageContainer);
        contentPanel.add(diagnosisPanel);
        
        // Bottom panel with buttons
        JPanel bottomPanel = new JPanel();
        bottomPanel.setBackground(new Color(250, 245, 230));
        
        RoundedButton viewDetailsBtn = new RoundedButton("View Full Output", new Color(135, 206, 235));
        viewDetailsBtn.setPreferredSize(new Dimension(180, 45));
        viewDetailsBtn.addActionListener(e -> {
            JDialog detailsDialog = new JDialog(resultsDialog, "Full Pipeline Output", true);
            detailsDialog.setSize(700, 500);
            detailsDialog.setLocationRelativeTo(resultsDialog);
            
            JTextArea fullOutput = new JTextArea(results);
            fullOutput.setEditable(false);
            fullOutput.setFont(new Font("Monospaced", Font.PLAIN, 12));
            JScrollPane scrollPane = new JScrollPane(fullOutput);
            
            detailsDialog.add(scrollPane);
            detailsDialog.setVisible(true);
        });
        
        RoundedButton closeBtn = new RoundedButton("Close", new Color(139, 195, 74));
        closeBtn.setPreferredSize(new Dimension(120, 45));
        closeBtn.addActionListener(e -> resultsDialog.dispose());
        
        bottomPanel.add(viewDetailsBtn);
        bottomPanel.add(Box.createHorizontalStrut(10));
        bottomPanel.add(closeBtn);
        
        // Assemble main panel
        mainPanel.add(title, BorderLayout.NORTH);
        mainPanel.add(contentPanel, BorderLayout.CENTER);
        mainPanel.add(bottomPanel, BorderLayout.SOUTH);
        
        resultsDialog.add(mainPanel);
        resultsDialog.setVisible(true);
    }
    
    // Show My Trees Panel
    private static void showMyTreesPanel(JFrame dashboard, String username, String password) {
        JDialog dialog = new JDialog(dashboard, "My Trees", true);
        dialog.setSize(700, 500);
        dialog.setLocationRelativeTo(dashboard);
        
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(new Color(250, 245, 230));
        panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        
        JLabel title = new JLabel("Your Tree Collection");
        title.setFont(new Font("SansSerif", Font.BOLD, 22));
        title.setForeground(new Color(45, 60, 30));
        title.setBorder(BorderFactory.createEmptyBorder(0, 0, 20, 0));
        
        JTextArea treesArea = new JTextArea(15, 50);
        treesArea.setEditable(false);
        treesArea.setFont(new Font("SansSerif", Font.PLAIN, 13));
        treesArea.setText("Loading your trees...\n");
        treesArea.setBackground(Color.WHITE);
        JScrollPane scrollPane = new JScrollPane(treesArea);
        
        // Load images in background
        new Thread(() -> {
            String response = loadUserImages(username, password);
            SwingUtilities.invokeLater(() -> treesArea.setText(response));
        }).start();
        
        panel.add(title, BorderLayout.NORTH);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        dialog.add(panel);
        dialog.setVisible(true);
    }
    
    // Show Species Detection Panel
    private static void showSpeciesPanel(JFrame dashboard, String username, String password) {
        JDialog dialog = new JDialog(dashboard, "Species Identification", true);
        dialog.setSize(500, 400);
        dialog.setLocationRelativeTo(dashboard);
        
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBackground(new Color(250, 245, 230));
        panel.setBorder(BorderFactory.createEmptyBorder(30, 40, 30, 40));
        
        JLabel title = new JLabel("Identify Tree Species");
        title.setFont(new Font("SansSerif", Font.BOLD, 22));
        title.setForeground(new Color(45, 60, 30));
        title.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel instruction = new JLabel("Upload a clear photo of the tree's leaves or bark");
        instruction.setFont(new Font("SansSerif", Font.PLAIN, 14));
        instruction.setForeground(new Color(100, 100, 100));
        instruction.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        JLabel selectedLabel = new JLabel("No image selected");
        selectedLabel.setFont(new Font("SansSerif", Font.PLAIN, 13));
        selectedLabel.setForeground(new Color(150, 150, 150));
        selectedLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        final File[] selectedFile = new File[1];
        
        RoundedButton selectBtn = new RoundedButton("Select Image", new Color(135, 206, 235));
        selectBtn.setMaximumSize(new Dimension(200, 45));
        selectBtn.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        selectBtn.addActionListener(e -> {
            JFileChooser fc = new JFileChooser();
            fc.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter(
                "Images", "jpg", "jpeg", "png", "gif"));
            if (fc.showOpenDialog(dialog) == JFileChooser.APPROVE_OPTION) {
                selectedFile[0] = fc.getSelectedFile();
                selectedLabel.setText("✓ " + fc.getSelectedFile().getName());
                selectedLabel.setForeground(new Color(76, 175, 80));
            }
        });
        
        RoundedButton identifyBtn = new RoundedButton("Identify Species", new Color(139, 195, 74));
        identifyBtn.setMaximumSize(new Dimension(200, 45));
        identifyBtn.setAlignmentX(Component.CENTER_ALIGNMENT);
        
        identifyBtn.addActionListener(e -> {
            if (selectedFile[0] == null) {
                JOptionPane.showMessageDialog(dialog, "Please select an image first!");
                return;
            }
            
            // TODO: Upload and identify species
            JOptionPane.showMessageDialog(dialog, "Species identification feature coming soon!");
            dialog.dispose();
        });
        
        panel.add(title);
        panel.add(Box.createVerticalStrut(10));
        panel.add(instruction);
        panel.add(Box.createVerticalStrut(40));
        panel.add(selectBtn);
        panel.add(Box.createVerticalStrut(15));
        panel.add(selectedLabel);
        panel.add(Box.createVerticalStrut(30));
        panel.add(identifyBtn);
        
        dialog.add(panel);
        dialog.setVisible(true);
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
                System.out.println("[INFO] Logo loaded from: " + logoFile.getAbsolutePath());
            } else {
                System.err.println("[ERROR] Logo.png not found at: " + logoFile.getAbsolutePath());
                System.err.println("[INFO] Current working directory: " + System.getProperty("user.dir"));
                System.err.println("[INFO] Looking for Logo in: " + BASE_DIR.getAbsolutePath());
            }
        } catch (Exception e) {
            System.err.println("[ERROR] Could not load logo: " + e.getMessage());
            e.printStackTrace();
        }

        // LEFT PANEL - Benefits with logo
        JPanel leftPanel = new JPanel();
        leftPanel.setBackground(new Color(135, 206, 235));
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
                System.out.println("[INFO] Left panel logo loaded successfully");
            } else {
                System.err.println("[ERROR] Logo.png not found at: " + logoFile.getAbsolutePath());
                JLabel fallbackLogo = new JLabel("🌲");
                fallbackLogo.setFont(new Font("SansSerif", Font.PLAIN, 100));
                fallbackLogo.setAlignmentX(Component.CENTER_ALIGNMENT);
                leftPanel.add(fallbackLogo);
                leftPanel.add(Box.createVerticalStrut(30));
            }
        } catch (Exception e) {
            System.err.println("[ERROR] Could not load logo for left panel: " + e.getMessage());
        }
        
        JLabel benefitsTitle = new JLabel("Join VitalArbor and get access to:");
        benefitsTitle.setFont(new Font("SansSerif", Font.BOLD, 20));
        benefitsTitle.setForeground(new Color(45, 60, 30));
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
            benefitLabel.setForeground(new Color(60, 80, 40));
            benefitLabel.setAlignmentX(Component.CENTER_ALIGNMENT);
            leftPanel.add(benefitLabel);
            leftPanel.add(Box.createVerticalStrut(12));
        }

        // RIGHT PANEL - Login Form
        JPanel rightPanel = new JPanel();
        rightPanel.setBackground(new Color(250, 245, 230));
        rightPanel.setLayout(new BoxLayout(rightPanel, BoxLayout.Y_AXIS));
        rightPanel.setBorder(BorderFactory.createEmptyBorder(40, 50, 40, 50));
        
        // Title
        JLabel titleLabel = new JLabel("Sign In");
        titleLabel.setFont(new Font("SansSerif", Font.BOLD, 32));
        titleLabel.setForeground(new Color(45, 60, 30));
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
        
        // Sign In button
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
        
        // Sign Up link
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
        
        // Guest button
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