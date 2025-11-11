// src/amplifyConfig.js
import { Amplify } from 'aws-amplify';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID, // <-- อ่านจาก .env
      userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID, // <-- อ่านจาก .env
    }
  }
});