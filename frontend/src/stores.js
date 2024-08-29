import { writable } from "svelte/store";

export const session = writable(null);
export const API_URL = "adjudicator-new-new-qiclexggp-rodavelis-projects.vercel.app";
// export const API_URL = "http://localhost:8000";

function getUserId() {
  let userId = localStorage.getItem("userId");
  if (!userId) {
    userId = "user_" + Math.random().toString(36).substr(2, 9);
    localStorage.setItem("userId", userId);
  }
  return userId;
}

export async function createSession(name, description) {
  const userId = getUserId();
  try {
    const response = await fetch(`${API_URL}/sessions/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, description, userId }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    session.set(data);
    return data;
  } catch (error) {
    console.error("Error creating session:", error);
    throw error;
  }
}

export async function getSession(id) {
  const userId = getUserId();
  try {
    const response = await fetch(`${API_URL}/sessions/${id}?userId=${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    session.set(data);
    return data;
  } catch (error) {
    console.error("Error fetching session:", error);
    throw error;
  }
}

export async function inviteUser(sessionId, email) {
  const userId = getUserId();
  try {
    const response = await fetch(`${API_URL}/sessions/${sessionId}/invite/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, userId }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error inviting user:", error);
    throw error;
  }
}

export async function submitArgument(sessionId, content, imageFile) {
  const userId = getUserId();
  const username = localStorage.getItem("username") || "Anonymous";
  console.log("Submitting argument:", {
    sessionId,
    content,
    imageFile,
    userId,
    username,
  });
  try {
    const formData = new FormData();
    formData.append("content", content);
    formData.append("userId", userId);
    formData.append("username", username);
    if (imageFile) {
      formData.append("image", imageFile);
    }

    const response = await fetch(
      `${API_URL}/sessions/${sessionId}/arguments/`,
      {
        method: "POST",
        body: formData,
      },
    );
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(
        `HTTP error! status: ${response.status}, message: ${JSON.stringify(errorData)}`,
      );
    }
    const data = await response.json();
    console.log("Argument submitted successfully:", data);

    session.update((s) => {
      if (s && s.id === sessionId) {
        return {
          ...s,
          arguments: [...(s.arguments || []), data],
        };
      }
      return s;
    });

    return data;
  } catch (error) {
    console.error("Error submitting argument:", error);
    throw error;
  }
}

export async function getJudgement(sessionId) {
  const userId = getUserId();
  try {
    const response = await fetch(`${API_URL}/sessions/${sessionId}/judge/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ userId }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const judgement = await response.json();
    session.update((s) => {
      if (s && s.id === sessionId) {
        return {
          ...s,
          judgement: judgement,
        };
      }
      return s;
    });
    return judgement;
  } catch (error) {
    console.error("Error getting judgement:", error);
    throw error;
  }
}

export async function updateUsername(sessionId, user, username) {
  const userId = getUserId();
  try {
    const response = await fetch(
      `${API_URL}/sessions/${sessionId}/update_username`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user, username, userId }),
      },
    );
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    localStorage.setItem("username", username);
    session.set(data);
    return data;
  } catch (error) {
    console.error("Error updating username:", error);
    throw error;
  }
}

export async function submitAppeal(sessionId, content) {
  const userId = getUserId();
  try {
    const response = await fetch(`${API_URL}/sessions/${sessionId}/appeal/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ content, userId }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    session.update((s) => ({ ...s, appeals: [...(s.appeals || []), data] }));
    return data;
  } catch (error) {
    console.error("Error submitting appeal:", error);
    throw error;
  }
}
