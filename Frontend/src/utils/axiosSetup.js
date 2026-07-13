import axios from "axios";

// The backend now requires a Bearer token on every data route (attendance is exactly the
// thing people have an incentive to cheat, and those routes used to be wide open).
//
// The pages call axios directly in ~14 places rather than going through utils/api.js, so
// attaching the token here — once, globally — is what keeps them all working instead of
// every page 401-ing. Any future axios call is covered automatically.
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// An expired or missing token means the session is over — send the user back to the login
// page rather than leaving every page silently empty.
//
// The login screen is mounted at "/login" (see App.jsx); "/" is the public landing page.
// This constant MUST track that route: pointing it at a path that does not exist silently
// wipes the token and redirects nowhere, and every later request 401s.
const LOGIN_PATH = "/login";

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== LOGIN_PATH) {
        window.location.href = LOGIN_PATH;
      }
    }
    return Promise.reject(error);
  }
);

export default axios;
