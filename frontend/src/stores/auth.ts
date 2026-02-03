import axios from "axios";
import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { useSettingsStore } from "../stores/settings";

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: import.meta.env.VITE_IVISION_API_BASE_URL || "http://localhost:8000",
});

// Flag to track if interceptors have been set up
let interceptorsSetUp = false;

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("token"));
  const refreshToken = ref(localStorage.getItem("refreshToken"));
  const user = ref(JSON.parse(localStorage.getItem("user") || "null"));
  const isRefreshing = ref(false);
  const refreshSubscribers = ref<((token: string) => void)[]>([]);
  const adminStatus = ref<boolean | null>(null); // Track admin status separately

  // Computed property for easy access to admin status
  const isAdmin = computed(() => {
    // First check the locally stored user data
    if (user.value?.is_admin !== undefined) {
      return user.value.is_admin;
    }
    // Fall back to the separately tracked admin status
    return adminStatus.value || false;
  });

  // Set up interceptors only once
  if (!interceptorsSetUp) {
    // Add request interceptor to include auth token
    api.interceptors.request.use(
      (config) => {
        const currentToken = localStorage.getItem("token");
        if (
          currentToken &&
          !config.url?.includes("/login") &&
          !config.url?.includes("/refresh")
        ) {
          config.headers.Authorization = `Bearer ${currentToken}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      },
    );

    // Add response interceptor to handle token refresh
    api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        const currentRefreshToken = localStorage.getItem("refreshToken");

        if (
          error.response?.status === 401 &&
          !originalRequest._retry &&
          currentRefreshToken &&
          !originalRequest.url?.includes("/login") &&
          !originalRequest.url?.includes("/refresh")
        ) {
          if (isRefreshing.value) {
            // If already refreshing, wait for the new token
            return new Promise((resolve) => {
              subscribeTokenRefresh((newToken: string) => {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                resolve(api(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          isRefreshing.value = true;

          try {
            const response = await api.post("/api/v1/refresh", {
              refresh_token: currentRefreshToken,
            });

            const { access_token, refresh_token } = response.data;
            token.value = access_token;
            refreshToken.value = refresh_token;

            localStorage.setItem("token", access_token);
            localStorage.setItem("refreshToken", refresh_token);

            // Notify all waiting requests
            onRefreshed(access_token);

            // Retry the original request
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return api(originalRequest);
          } catch (refreshError) {
            // If refresh fails, logout user
            logout();
            return Promise.reject(refreshError);
          } finally {
            isRefreshing.value = false;
          }
        }

        return Promise.reject(error);
      },
    );

    interceptorsSetUp = true;
  }

  const subscribeTokenRefresh = (cb: (token: string) => void) => {
    refreshSubscribers.value.push(cb);
  };

  const onRefreshed = (newToken: string) => {
    refreshSubscribers.value.forEach((cb) => cb(newToken));
    refreshSubscribers.value = [];
  };

  const login = async (email: string, password: string) => {
    try {
      console.log("Login process started");
      const response = await api.post("/api/v1/login", {
        email,
        password,
      });

      console.log("Login API response received:", response.status);

      const { access_token, refresh_token, user: userData } = response.data;
      token.value = access_token;
      refreshToken.value = refresh_token;
      user.value = userData;

      // Update admin status from user data
      adminStatus.value = userData?.is_admin || false;

      localStorage.setItem("token", access_token);
      localStorage.setItem("refreshToken", refresh_token);
      localStorage.setItem("user", JSON.stringify(userData));

      console.log("Tokens stored in localStorage");
      console.log("Admin status:", adminStatus.value);

      // Initialize settings after login
      const settingsStore = useSettingsStore();
      await settingsStore.initialize();

      console.log("Settings initialized, login complete");

      return response.data;
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    }
  };

  const logout = async () => {
    console.log("Logout function called");
    console.log("Stack trace:", new Error().stack); // This will show where logout is being called from

    try {
      // Try to call logout endpoint if token is still valid
      const currentToken = localStorage.getItem("token");
      if (currentToken) {
        console.log("Calling logout API endpoint");
        await api.post("/api/v1/logout");
        console.log("Logout API call successful");
      }
    } catch (error) {
      console.error("Logout API call failed:", error);
    } finally {
      console.log("Clearing local auth state");
      // Clear local state regardless of API call result
      token.value = null;
      refreshToken.value = null;
      user.value = null;
      adminStatus.value = null;
      localStorage.removeItem("token");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("user");
      console.log("Local auth state cleared");
    }
  };

  const refresh = async () => {
    const currentRefreshToken = localStorage.getItem("refreshToken");
    if (!currentRefreshToken) {
      throw new Error("No refresh token available");
    }

    const response = await api.post("/api/v1/refresh", {
      refresh_token: currentRefreshToken,
    });

    const { access_token, refresh_token } = response.data;
    token.value = access_token;
    refreshToken.value = refresh_token;

    localStorage.setItem("token", access_token);
    localStorage.setItem("refreshToken", refresh_token);

    return response.data;
  };

  // New method to check admin status from server
  const checkAdminStatus = async (): Promise<boolean> => {
    try {
      const response = await api.get("/api/v1/is-admin");

      const { is_admin } = response.data;

      // Update both the user object and the separate admin status
      if (user.value) {
        user.value.is_admin = is_admin;
        localStorage.setItem("user", JSON.stringify(user.value));
      }
      adminStatus.value = is_admin;

      console.log("Admin status checked:", is_admin);
      return is_admin;
    } catch (error: any) {
      console.error("Failed to check admin status:", error);

      // If the request fails due to auth, we might not be admin
      if (error.response?.status === 401 || error.response?.status === 403) {
        adminStatus.value = false;
        return false;
      }

      // For other errors, we'll return the current cached status
      return isAdmin.value;
    }
  };

  // Initialize admin status from localStorage on store creation
  const initializeAdminStatus = () => {
    if (user.value?.is_admin !== undefined) {
      adminStatus.value = user.value.is_admin;
    } else {
      adminStatus.value = false;
    }
  };

  // Call initialization
  initializeAdminStatus();

  const isAuthenticated = () => !!token.value;

  return {
    token,
    refreshToken,
    user,
    login,
    logout,
    refresh,
    isAuthenticated,
    isAdmin, // Export computed property
    adminStatus, // Export ref for direct access if needed
    checkAdminStatus, // Export method to check admin status
  };
});
