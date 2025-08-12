import { PublicClientApplication } from "@azure/msal-browser";

let redirectUri = "";
if (import.meta.env.VITE_ENV == "production") {
  redirectUri = "https://www.ekilibria.tech/auth-callback";
}else if (import.meta.env.VITE_ENV == "render") {
  redirectUri = "http://www.ekilibria.onrender.com/auth-callback";
}else {
  redirectUri = "http://localhost:5002/auth-callback";
}

const msalConfig = {
  auth: {
    clientId: "845ac38e-8122-4897-939d-0532d48feb95",
    authority: "https://login.microsoftonline.com/common",
    redirectUri: redirectUri
  }
};

export const msalInstance = new PublicClientApplication(msalConfig);

