const API_URL = "http://localhost:5000";

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

// Register new student
export const registerStudent = async (name, images) => {
  try {
    const response = await fetch(`${API_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
      headers: { "Content-Type": "application/json" },
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
    const response = await fetch(`${API_URL}/attendance`);
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
    const response = await fetch(`${API_URL}/students`);
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
    const response = await fetch(`${API_URL}/students/valid-names`);
    if (!response.ok) throw new Error(`Failed to fetch valid names: ${response.status}`);
    
    const data = await response.json();
    console.log("✅ Valid student names:", data.valid_names);
    return data;
  } catch (error) {
    console.error("❌ Valid names fetch error:", error);
    throw error;
  }
};

// Update student with more images
export const updateStudent = async (name, images) => {
  try {
    const response = await fetch(`${API_URL}/update-student`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
    });
    
    if (!response.ok) throw new Error(`Clear attendance failed: ${response.status}`);
    
    return response.json();
  } catch (error) {
    console.error("❌ Clear attendance error:", error);
    throw error;
  }
};
