/**
 * Cloudflare Worker: TriForce Load Balancer
 * 
 * Features:
 * - Dynamic backend selection based on model
 * - Health-check aware routing
 * - Weighted round-robin
 * - Failover support
 */

// Backend configuration - fetched from Hub periodically
let BACKENDS = {
  hetzner: {
    url: 'https://api.ailinux.me',
    weight: 100,
    healthy: true,
    models: ['*']  // All models
  },
  backup: {
    url: 'http://5.104.107.103:9000',
    weight: 50,
    healthy: true,
    models: ['*']
  }
};

// Cache for backend config (refresh every 60s)
let lastConfigFetch = 0;
const CONFIG_TTL = 60000;

/**
 * Fetch backend config from Hub
 */
async function refreshConfig() {
  const now = Date.now();
  if (now - lastConfigFetch < CONFIG_TTL) return;
  
  try {
    const response = await fetch('https://api.ailinux.me/v1/federation/lb/cloudflare', {
      headers: { 'X-Worker-Auth': 'triforce-lb-2025' }
    });
    
    if (response.ok) {
      const config = await response.json();
      if (config.backends) {
        BACKENDS = {};
        for (const b of config.backends) {
          BACKENDS[b.id] = {
            url: b.url,
            weight: b.weight,
            healthy: b.healthy,
            models: b.models || ['*']
          };
        }
      }
      lastConfigFetch = now;
    }
  } catch (e) {
    console.error('Config refresh failed:', e);
  }
}

/**
 * Select best backend for request
 */
function selectBackend(model) {
  const candidates = [];
  
  for (const [id, backend] of Object.entries(BACKENDS)) {
    if (!backend.healthy || backend.weight <= 0) continue;
    
    // Check if backend supports the model
    const supportsModel = backend.models.includes('*') || 
                          backend.models.includes(model) ||
                          !model;
    
    if (supportsModel) {
      candidates.push({ id, ...backend });
    }
  }
  
  if (candidates.length === 0) {
    // Fallback to any backend
    return Object.values(BACKENDS)[0];
  }
  
  // Weighted random selection
  const totalWeight = candidates.reduce((sum, b) => sum + b.weight, 0);
  let random = Math.random() * totalWeight;
  
  for (const candidate of candidates) {
    random -= candidate.weight;
    if (random <= 0) {
      return candidate;
    }
  }
  
  return candidates[0];
}

/**
 * Main request handler
 */
async function handleRequest(request) {
  // Refresh config periodically
  await refreshConfig();
  
  const url = new URL(request.url);
  
  // Health check endpoint
  if (url.pathname === '/lb/health') {
    return new Response(JSON.stringify({
      status: 'ok',
      backends: Object.entries(BACKENDS).map(([id, b]) => ({
        id,
        healthy: b.healthy,
        weight: b.weight
      }))
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  // Extract model from request
  let model = request.headers.get('X-Model') || '';
  
  // For chat requests, try to get model from body
  if (url.pathname.includes('/chat') && request.method === 'POST') {
    try {
      const body = await request.clone().json();
      model = body.model || model;
    } catch (e) {}
  }
  
  // Select backend
  const backend = selectBackend(model);
  
  if (!backend) {
    return new Response(JSON.stringify({
      error: 'No available backend'
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  // Forward request to backend
  const backendUrl = new URL(url.pathname + url.search, backend.url);
  
  const modifiedRequest = new Request(backendUrl, {
    method: request.method,
    headers: request.headers,
    body: request.body,
    redirect: 'follow'
  });
  
  // Add routing headers
  modifiedRequest.headers.set('X-Forwarded-For', request.headers.get('CF-Connecting-IP') || '');
  modifiedRequest.headers.set('X-Backend-ID', backend.id || 'unknown');
  
  try {
    const response = await fetch(modifiedRequest);
    
    // Clone response and add headers
    const modifiedResponse = new Response(response.body, response);
    modifiedResponse.headers.set('X-Backend', backend.id || 'unknown');
    
    return modifiedResponse;
    
  } catch (e) {
    // Mark backend as unhealthy
    if (BACKENDS[backend.id]) {
      BACKENDS[backend.id].healthy = false;
    }
    
    // Try another backend
    const fallback = selectBackend(model);
    if (fallback && fallback.id !== backend.id) {
      const fallbackUrl = new URL(url.pathname + url.search, fallback.url);
      return fetch(new Request(fallbackUrl, modifiedRequest));
    }
    
    return new Response(JSON.stringify({
      error: 'Backend unavailable',
      message: e.message
    }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
