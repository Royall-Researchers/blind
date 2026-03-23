import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';

async function startServer() {
  const app = express();
  const port = 3000;

  // Use the platform-provided GEMINI_API_KEY
  const apiKey = process.env.GEMINI_API_KEY ? process.env.GEMINI_API_KEY.trim() : null;
  
  if (!apiKey) {
    console.error("[Node] CRITICAL ERROR: GEMINI_API_KEY is not defined in the environment.");
  } else {
    const maskedKey = apiKey.substring(0, 4) + "..." + apiKey.substring(apiKey.length - 4);
    console.log("[Node] GEMINI_API_KEY is present. Length: " + apiKey.length + " | Masked: " + maskedKey);
    
    if (apiKey === "your_api_key_here") {
      console.error("[Node] CRITICAL ERROR: GEMINI_API_KEY is still the placeholder value!");
    }
  }

  app.use(express.json({ limit: '50mb' }));

  // Vite middleware for development
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(port, '0.0.0.0', () => {
    console.log(`[Node] Server running on http://localhost:${port}`);
  });
}

startServer();
