const fs = require("fs");
const admin = require("firebase-admin");
const bcrypt = require("bcryptjs");

// Initialize Firebase with service account
const serviceAccount = require("./serviceAccountKey.json");

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  storageBucket: "vitalarbor-17297.appspot.com"
});

const db = admin.firestore();

// Load users.txt
const file = "users.txt";

// Check if users.txt exists
if (!fs.existsSync(file)) {
  console.log("❌ users.txt not found. Creating empty file...");
  fs.writeFileSync(file, "");
  console.log("Please add users in format: username:password (one per line)");
  process.exit(0);
}

const lines = fs.readFileSync(file, "utf-8").trim().split("\n");

(async () => {
  for (const line of lines) {
    if (!line.trim()) continue; // Skip empty lines
    
    const [username, password] = line.split(":");
    if (!username || !password) {
      console.log(`⚠️ Skipping invalid line: ${line}`);
      continue;
    }

    const userRef = db.collection("users").doc(username.trim());
    const doc = await userRef.get();
    
    if (doc.exists) {
      console.log(`⏭️ Skipping ${username}, already exists.`);
      continue;
    }

    const passwordHash = await bcrypt.hash(password.trim(), 12);
    await userRef.set({
      username: username.trim(),
      passwordHash,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      images: [] // Array to store user's tree image references
    });

    console.log(`✅ Migrated ${username}`);
  }
  console.log("✨ Migration complete.");
  process.exit(0);
})();