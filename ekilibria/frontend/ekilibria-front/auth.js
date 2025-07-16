import { PublicClientApplication } from "@azure/msal-browser";

const msalConfig = {
  auth: {
    clientId: "845ac38e-8122-4897-939d-0532d48feb95",
    authority: "https://login.microsoftonline.com/common",
    redirectUri: "https://ekilibria.onrender.com/auth-callback"
  }
};

export const msalInstance = new PublicClientApplication(msalConfig);

