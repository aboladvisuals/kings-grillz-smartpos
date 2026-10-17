import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.kingsgrillz.smartpos',
  appName: "KING'S GRILLZ SmartPOS",
  webDir: 'dist',
  server: {
    url: 'https://kings-grillz.onrender.com',
    cleartext: false,
    androidScheme: 'https'
  }
};

export default config;
