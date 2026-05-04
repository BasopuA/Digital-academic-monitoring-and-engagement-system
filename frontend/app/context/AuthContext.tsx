"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";

// Types
export interface User {
  id: number;
  username: string;
  email?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Initialize auth state from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("edutracksa_token");
    const storedUser = localStorage.getItem("edutracksa_user");
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Login failed");
      }

      const data = await response.json();
      
      // Store token and user
      localStorage.setItem("edutracksa_token", data.access_token);
      localStorage.setItem("edutracksa_user", JSON.stringify({ 
        username,
        id: 1, 
        is_active: true,
        is_admin: false,
        created_at: new Date().toISOString()
      }));
      
      setToken(data.access_token);
      
      // Fetch user profile
      await fetchUserProfile(data.access_token);
      
      
      router.push("/learner-dashbord");
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUserProfile = async (accessToken: string) => {
    try {
      const response = await fetch(`${API_URL}/users/me`, {
        headers: {
          "Authorization": `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        localStorage.setItem("edutracksa_user", JSON.stringify(userData));
      }
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
    }
  };

  const logout = () => {
    localStorage.removeItem("edutracksa_token");
    localStorage.removeItem("edutracksa_user");
    setToken(null);
    setUser(null);
    router.push("/login");
  };

  const value = {
    user,
    token,
    isLoading,
    login,
    logout,
    isAuthenticated: !!token && !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}