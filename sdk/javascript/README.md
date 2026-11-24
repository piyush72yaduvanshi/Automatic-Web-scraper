# AI Sales CRM OS — JavaScript / Node.js SDK

Official Node.js and Browser SDK for AI Sales CRM OS.

## 📦 Installation
```bash
npm install @aisalescrm/sdk
# or directly require/import from local workspace
```

## 🚀 Quick Usage

```javascript
const { AiSalesCrm } = require('./index.js');

const crm = new AiSalesCrm({
  baseUrl: 'http://localhost:8000',
  apiKey: 'optional_api_key',
});

// 1. Ingest a lead from your web app or form
async function run() {
  const result = await crm.ingestLead({
    business_name: 'Max Healthcare Centre',
    category: 'Hospital',
    phone: '+91 522 223344',
    email: 'info@maxhealth.in',
    city: 'Lucknow',
  });
  console.log('Ingested lead ID:', result.lead.id);

  // 2. Discover local leads via Google Maps engine
  const discovery = await crm.discoverLeads({
    query: 'Orthopedic Doctors',
    location: 'Lucknow',
    limit: 5,
  });
  console.log('Discovered leads:', discovery.leads);
}

run();
```

## 🔒 Webhook Verification (Express.js Example)

```javascript
const express = require('express');
const { AiSalesCrm } = require('./index.js');

const app = express();
app.use(express.raw({ type: 'application/json' }));

app.post('/webhook', (req, res) => {
  const signature = req.headers['x-crm-signature'];
  const isValid = AiSalesCrm.verifyWebhookSignature(req.body, signature, process.env.WEBHOOK_SECRET);

  if (!isValid) {
    return res.status(401).json({ error: 'Invalid HMAC signature' });
  }

  const event = JSON.parse(req.body.toString('utf8'));
  console.log('Event received:', event.event, event.data);

  return res.json({ success: true });
});

app.listen(3000);
```
