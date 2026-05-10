"use client";

import React from "react";
import { Typography, Box, Button, Container, Paper } from "@mui/material";
import { useAuth } from "@/app/context/AuthContext";
import { useRouter } from "next/navigation";

export default function LuphawuDashboard() {
  const { user, logout, isAuthenticated } = useAuth();
  const router = useRouter();

  // Protect route
  React.useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated || !user) {
    return (
      <Box sx={{ p: 4, textAlign: "center" }}>
        <Typography>Loading Luphawu Dashboard...</Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 4 }}>
          <Typography variant="h4" component="h1">
            🎓 Luphawu Dashboard
          </Typography>
          <Button variant="outlined" color="secondary" onClick={logout}>
            Sign Out
          </Button>
        </Box>

        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6">Welcome, {user.username}! 👋</Typography>
          <Typography variant="body1" color="textSecondary">
            Manage your academic engagement and monitoring from here.
          </Typography>
        </Paper>

        {/* Add your dashboard widgets here */}
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(3, 1fr)" }, gap: 2 }}>
          {/* Example cards */}
          {[
            { title: "Active Courses", value: "5", color: "primary" },
            { title: "Pending Tasks", value: "12", color: "warning" },
            { title: "Completion Rate", value: "78%", color: "success" },
          ].map((card) => (
            <Paper 
              key={card.title} 
              elevation={1} 
              sx={{ 
                p: 3, 
                borderLeft: `4px solid`,
                borderColor: `${card.color}.main`
              }}
            >
              <Typography variant="body2" color="textSecondary">
                {card.title}
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                {card.value}
              </Typography>
            </Paper>
          ))}
        </Box>
      </Box>
    </Container>
  );
}