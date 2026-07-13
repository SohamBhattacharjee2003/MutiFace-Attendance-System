// Same-origin by default. In dev, Vite proxies these to the Flask server (vite.config.js);
// in production Flask serves the built frontend itself, so "" resolves to the right host —
// including over a Cloudflare tunnel. A hardcoded localhost:5000 would mean "the student's
// own phone" the moment the link leaves this machine.
const API_URL = import.meta.env.VITE_API_URL ?? "/api";

// Every data endpoint on the backend now requires a Bearer token. Attendance is the
// thing people have an incentive to cheat, and these routes used to be wide open —
// anyone on the same network could mark themselves present or delete a student.
const authHeaders = (extra = {}) => {
  const token = localStorage.getItem("token");
  return {
    ...extra,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};


// Health check
export const checkHealth = async () => {
  try {
    const response = await fetch(`${API_URL}/health`);
    if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
    return response.json();
  } catch (error) {
    console.error("❌ Health check error:", error);
    throw error;
  }
};

// ==================== AUTH API ====================

// User Signup
export const signup = async (name, email, password) => {
  try {
    const response = await fetch(`${API_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `Signup failed: ${response.status}`);
    }

    // Store token in localStorage
    if (data.token) {
      localStorage.setItem("token", data.token);
      localStorage.setItem("user", JSON.stringify(data.user));
    }

    return data;
  } catch (error) {
    console.error("❌ Signup error:", error);
    throw error;
  }
};

// User Login
export const login = async (email, password) => {
  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `Login failed: ${response.status}`);
    }

    // Store token in localStorage
    if (data.token) {
      localStorage.setItem("token", data.token);
      localStorage.setItem("user", JSON.stringify(data.user));
    }

    return data;
  } catch (error) {
    console.error("❌ Login error:", error);
    throw error;
  }
};

// Verify Token
export const verifyToken = async () => {
  try {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("No token found");

    const response = await fetch(`${API_URL}/auth/verify`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      throw new Error("Token verification failed");
    }

    return response.json();
  } catch (error) {
    console.error("❌ Token verification error:", error);
    throw error;
  }
};

// Get Current User
export const getCurrentUser = async () => {
  try {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("No token found");

    const response = await fetch(`${API_URL}/auth/me`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to get user data");
    }

    return response.json();
  } catch (error) {
    console.error("❌ Get user error:", error);
    throw error;
  }
};

// Logout
export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
};

// Register new student
export const registerStudent = async (name, images) => {
  try {
    const response = await fetch(`${API_URL}/register`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ name, images }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Registration failed: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    console.error("❌ Registration error:", error);
    throw error;
  }
};

// Predict face from image
export const predictFace = async (imageBase64) => {
  try {
    const response = await fetch(`${API_URL}/predict`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ image: imageBase64 }),
    });
    
    if (!response.ok) {
      throw new Error(`Prediction failed: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log("✅ Prediction response:", data);
    return data;
  } catch (error) {
    console.error("❌ Prediction error:", error);
    throw error;
  }
};

// Get attendance records
export const getAttendance = async () => {
  try {
    const response = await fetch(`${API_URL}/attendance`, { headers: authHeaders() });
    if (!response.ok) throw new Error(`Failed to fetch attendance: ${response.status}`);
    
    const data = await response.json();
    console.log("✅ Attendance data fetched:", data.length, "records");
    return data;
  } catch (error) {
    console.error("❌ Attendance fetch error:", error);
    throw error;
  }
};

// Get students list
export const getStudents = async () => {
  try {
    const response = await fetch(`${API_URL}/students`, { headers: authHeaders() });
    if (!response.ok) throw new Error(`Failed to fetch students: ${response.status}`);
    
    const data = await response.json();
    console.log("✅ Students data fetched:", data.length, "students");
    return data;
  } catch (error) {
    console.error("❌ Students fetch error:", error);
    throw error;
  }
};

// Get valid student names (with embeddings)
export const getValidStudentNames = async () => {
  try {
    const response = await fetch(`${API_URL}/students/valid-names`, { headers: authHeaders() });
    if (!response.ok) throw new Error(`Failed to fetch valid names: ${response.status}`);
    
    const data = await response.json();
    console.log("✅ Valid student names:", data.valid_names);
    return data;
  } catch (error) {
    console.error("❌ Valid names fetch error:", error);
    throw error;
  }
};

// Training status — poll after registering; status goes "training" -> "done".
// A student is only recognizable once the retrain that follows their registration
// reaches "done"; until then /predict still returns "Unknown" for them.
export const getTrainingStatus = async () => {
  try {
    const response = await fetch(`${API_URL}/train/status`, { headers: authHeaders() });
    if (!response.ok) throw new Error(`Failed to fetch training status: ${response.status}`);
    return response.json();
  } catch (error) {
    console.error("❌ Training status error:", error);
    throw error;
  }
};

// Update student with more images
export const updateStudent = async (name, images) => {
  try {
    const response = await fetch(`${API_URL}/update-student`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ name, images }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Update failed: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    console.error("❌ Update student error:", error);
    throw error;
  }
};

// Delete student
export const deleteStudent = async (name) => {
  try {
    const response = await fetch(`${API_URL}/students/${name}`, {
      method: "DELETE",
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Delete failed: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    console.error("❌ Delete student error:", error);
    throw error;
  }
};

// Clear all attendance records
export const clearAttendance = async () => {
  try {
    const response = await fetch(`${API_URL}/attendance/clear`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    
    if (!response.ok) throw new Error(`Clear attendance failed: ${response.status}`);
    
    return response.json();
  } catch (error) {
    console.error("❌ Clear attendance error:", error);
    throw error;
  }
};

// ==================== CLASSES ====================
// A teacher takes several classes; a student in one is not a student in another.

export const getClasses = async () => {
  const r = await fetch(`${API_URL}/classes`, { headers: authHeaders() });
  if (!r.ok) throw new Error("Failed to load classes");
  return r.json();
};

export const createClass = async (name) => {
  const r = await fetch(`${API_URL}/classes`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ name }),
  });
  if (!r.ok) throw new Error((await r.json()).error || "Failed to create class");
  return r.json();
};

export const getClass = async (id) => {
  const r = await fetch(`${API_URL}/classes/${id}`, { headers: authHeaders() });
  if (!r.ok) throw new Error("Class not found");
  return r.json();
};

export const deleteClass = async (id) => {
  const r = await fetch(`${API_URL}/classes/${id}`, {
    method: "DELETE", headers: authHeaders(),
  });
  if (!r.ok) throw new Error("Failed to delete class");
  return r.json();
};

// The roster is the security gate: only rolls the teacher publishes can self-enrol.
export const addToRoster = async (id, students) => {
  const r = await fetch(`${API_URL}/classes/${id}/roster`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ students }),
  });
  if (!r.ok) throw new Error("Failed to update roster");
  return r.json();
};

export const removeFromRoster = async (id, roll) => {
  const r = await fetch(`${API_URL}/classes/${id}/roster/${roll}`, {
    method: "DELETE", headers: authHeaders(),
  });
  if (!r.ok) throw new Error("Failed to remove student");
  return r.json();
};

export const getClassAttendance = async (id, date) => {
  const q = date ? `?date=${date}` : "";
  const r = await fetch(`${API_URL}/classes/${id}/attendance${q}`, { headers: authHeaders() });
  if (!r.ok) throw new Error("Failed to load attendance");
  return r.json();
};

export const getClassHistory = async (id, days = 30) => {
  const r = await fetch(`${API_URL}/classes/${id}/history?days=${days}`, {
    headers: authHeaders(),
  });
  if (!r.ok) throw new Error("Failed to load history");
  return r.json();
};

// ==================== PUBLIC SELF-ENROLMENT (no login) ====================
// The student opens a link the teacher shared. No account, no token.

// A roll number is an identity key. Students paste and mistype — trailing commas from a
// copied spreadsheet cell, stray spaces. Normalise exactly as the server does, so a
// student is never told "you are not on the roster" over a comma.
export const cleanRoll = (roll) => String(roll ?? "").trim().replace(/^[,;\s]+|[,;\s]+$/g, "");

export const getEnrollInfo = async (code) => {
  const r = await fetch(`${API_URL}/enroll/${code}`);
  if (!r.ok) throw new Error((await r.json()).error || "Invalid enrolment link");
  return r.json();
};

export const submitEnroll = async (code, roll, images) => {
  const r = await fetch(`${API_URL}/enroll/${code}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ roll: cleanRoll(roll), images }),
  });

  // If the server (or the tunnel in front of it) is down, the body is an HTML error page,
  // not JSON — and r.json() then throws "Unexpected token '<'", which tells the student
  // nothing. Read it as text first and give them something they can act on.
  const body = await r.text();
  let data;
  try {
    data = JSON.parse(body);
  } catch {
    throw new Error(
      r.status >= 500
        ? "The server isn't reachable. The link may have expired — ask your teacher for a fresh one."
        : "Unexpected response from the server. Please try again."
    );
  }
  if (!r.ok) throw new Error(data.error || "Enrolment failed");
  return data;
};

// ==================== REPORT DOWNLOAD ====================
// The export routes are behind auth, so a plain <a href> would 401 (a link carries no
// Authorization header). Fetch it with the token, then hand the browser a blob.
export const downloadReport = async (classId, format = "xlsx") => {
  const r = await fetch(`${API_URL}/classes/${classId}/export?format=${format}`, {
    headers: authHeaders(),
  });
  if (!r.ok) throw new Error("Could not generate the report");

  const blob = await r.blob();
  // Flask's send_file writes the filename UNQUOTED (filename=x.xlsx), while our CSV route
  // quotes it. Match both, or the download silently lands as a generic "attendance.xlsx".
  const cd = r.headers.get("Content-Disposition") || "";
  const name =
    /filename\*?=(?:UTF-8'')?"?([^";]+)"?/.exec(cd)?.[1]?.trim() ||
    `attendance.${format === "xlsx" ? "xlsx" : "csv"}`;

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  return name;
};
