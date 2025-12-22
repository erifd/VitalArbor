const express = require("express");
const admin = require("firebase-admin");
const bcrypt = require("bcryptjs");
const cors = require("cors");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
const multer = require("multer");

// ✅ Initialize Firebase with Service Account
const serviceAccount = require("./serviceAccountKey.json");

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  projectId: "vitalarbor-17297",
  storageBucket: "vitalarbor-17297.appspot.com",
  databaseURL: "https://vitalarbor-17297.firebaseio.com"
});

const db = admin.firestore();
const settings = { ignoreUndefinedProperties: true };
db.settings(settings);

// Test Firestore connection
// db.collection('test').doc('test').set({ test: 'test' })
//   .then(() => console.log('✅ Firestore connection test successful!'))
//   .catch(err => console.error('❌ Firestore connection test failed:', err));

const bucket = admin.storage().bucket();
const app = express();
const PORT = 3000;

// ✅ Configure multer for file uploads (memory storage)
const upload = multer({ 
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files allowed'));
    }
  }
});

// ✅ Middleware - CRITICAL ORDER!
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ✅ Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
});
app.use(limiter);

app.use(helmet({
  contentSecurityPolicy: false,
}));

// ----------------- ROUTES -----------------

// 🟢 Signup route
app.post("/api/signup", async (req, res) => {
  try {
    console.log("🔵 Signup request received");
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: "Username and password required" });
    }

    const userRef = db.collection("users").doc(username);
    const doc = await userRef.get();

    if (doc.exists) {
      return res.status(400).json({ error: "User already exists" });
    }

    const passwordHash = await bcrypt.hash(password, 12);
    
    await userRef.set({
      username,
      passwordHash,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      images: [] // Store tree image metadata
    });

    console.log("✅ Signup successful for:", username);
    res.json({ message: "Signup successful" });
  } catch (err) {
    console.error("❌ SIGNUP ERROR:", err);
    res.status(500).json({ error: "Internal server error", details: err.message });
  }
});

// 🔵 Login route
app.post("/api/login", async (req, res) => {
  try {
    console.log("🔵 Login request received");
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: "Username and password required" });
    }

    const userRef = db.collection("users").doc(username);
    const doc = await userRef.get();

    if (!doc.exists) {
      return res.status(400).json({ error: "Invalid credentials" });
    }

    const { passwordHash } = doc.data();
    const isMatch = await bcrypt.compare(password, passwordHash);

    if (!isMatch) {
      return res.status(400).json({ error: "Invalid credentials" });
    }

    console.log("✅ Login successful for:", username);
    res.json({ message: "Login successful", username });
  } catch (err) {
    console.error("❌ LOGIN ERROR:", err);
    res.status(500).json({ error: "Internal server error", details: err.message });
  }
});

// 📤 Upload tree image
app.post("/api/upload", upload.single('image'), async (req, res) => {
  try {
    console.log("📤 Upload request received");
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: "Username and password required" });
    }

    if (!req.file) {
      return res.status(400).json({ error: "No image file provided" });
    }

    // Verify credentials
    const userRef = db.collection("users").doc(username);
    const doc = await userRef.get();

    if (!doc.exists) {
      return res.status(400).json({ error: "User not found" });
    }

    const { passwordHash } = doc.data();
    const isMatch = await bcrypt.compare(password, passwordHash);

    if (!isMatch) {
      return res.status(400).json({ error: "Invalid credentials" });
    }

    // Upload to Firebase Storage
    const timestamp = Date.now();
    const filename = `${username}/${timestamp}_${req.file.originalname}`;
    const file = bucket.file(filename);

    await file.save(req.file.buffer, {
      metadata: {
        contentType: req.file.mimetype,
      },
    });

    // Make file publicly accessible (or use signed URLs for private access)
    await file.makePublic();
    const publicUrl = `https://storage.googleapis.com/${bucket.name}/${filename}`;

    // Save metadata to Firestore
    const imageData = {
      filename,
      url: publicUrl,
      uploadedAt: admin.firestore.FieldValue.serverTimestamp(),
      processed: false,
      results: null
    };

    await userRef.update({
      images: admin.firestore.FieldValue.arrayUnion(imageData)
    });

    console.log(`✅ Image uploaded for ${username}: ${filename}`);
    res.json({ 
      message: "Upload successful",
      imageUrl: publicUrl,
      filename
    });
  } catch (err) {
    console.error("❌ UPLOAD ERROR:", err);
    res.status(500).json({ error: "Internal server error", details: err.message });
  }
});

// 📂 Get user's images
app.post("/api/images", async (req, res) => {
  try {
    console.log("📂 Get images request received");
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: "Username and password required" });
    }

    // Verify credentials
    const userRef = db.collection("users").doc(username);
    const doc = await userRef.get();

    if (!doc.exists) {
      return res.status(400).json({ error: "User not found" });
    }

    const userData = doc.data();
    const isMatch = await bcrypt.compare(password, userData.passwordHash);

    if (!isMatch) {
      return res.status(400).json({ error: "Invalid credentials" });
    }

    console.log(`✅ Images loaded for ${username}: ${userData.images?.length || 0} images`);
    res.json({ 
      message: "Images loaded successfully",
      images: userData.images || []
    });
  } catch (err) {
    console.error("❌ LOAD IMAGES ERROR:", err);
    res.status(500).json({ error: "Internal server error", details: err.message });
  }
});

// 🔬 Process image (placeholder - add your processing logic here)
app.post("/api/process", async (req, res) => {
  try {
    console.log("🔬 Process request received");
    const { username, password, filename } = req.body;

    if (!username || !password || !filename) {
      return res.status(400).json({ error: "Username, password, and filename required" });
    }

    // Verify credentials
    const userRef = db.collection("users").doc(username);
    const doc = await userRef.get();

    if (!doc.exists) {
      return res.status(400).json({ error: "User not found" });
    }

    const userData = doc.data();
    const isMatch = await bcrypt.compare(password, userData.passwordHash);

    if (!isMatch) {
      return res.status(400).json({ error: "Invalid credentials" });
    }

    // TODO: Add your tree image processing logic here
    // This is where you'd analyze the tree image and return results
    
    const processedResults = {
      treeType: "Example Tree",
      health: "Good",
      estimatedAge: "10 years",
      // Add your actual processing results
    };

    // Update image metadata in Firestore
    const images = userData.images || [];
    const updatedImages = images.map(img => {
      if (img.filename === filename) {
        return { ...img, processed: true, results: processedResults };
      }
      return img;
    });

    await userRef.update({ images: updatedImages });

    console.log(`✅ Image processed for ${username}: ${filename}`);
    res.json({ 
      message: "Processing complete",
      results: processedResults
    });
  } catch (err) {
    console.error("❌ PROCESS ERROR:", err);
    res.status(500).json({ error: "Internal server error", details: err.message });
  }
});

// ----------------- START SERVER -----------------
app.listen(PORT, () => {
  console.log(`✅ VitalArbor API running on http://localhost:${PORT}`);
  console.log(`🔥 Firebase initialized successfully`);
  console.log(`📦 Storage bucket: ${bucket.name}`);
});