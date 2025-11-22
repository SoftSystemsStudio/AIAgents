#!/bin/bash
# Generate config.js from environment variables at build time

cat > config.js << EOF
// Contact form configuration - Generated at build time
window.APP_CONFIG = {
    WEB3FORMS_ACCESS_KEY: '${WEB3FORMS_ACCESS_KEY:-YOUR_KEY_HERE}'
};
EOF

echo "✅ Generated config.js with Web3Forms key"
