import { writable } from 'svelte/store';

const API_URL = 'http://localhost:8000';

export const session = writable(null);

export async function createSession(name, description) {
  try {
    const response = await fetch(`${API_URL}/sessions/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, description }),
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
  try {
    const response = await fetch(`${API_URL}/sessions/${id}`);
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
    try {
      const response = await fetch(`${API_URL}/sessions/${sessionId}/invite/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // Optionally update the session store if the API returns updated session data
      // session.update(s => ({ ...s, ...data }));
      return data;
    } catch (error) {
      console.error("Error inviting user:", error);
      throw error;
    }
  }

export async function submitArgument(sessionId, content, imageFile) {
    console.log('Submitting argument:', { sessionId, content, imageFile });
    try {
      const formData = new FormData();
      formData.append('content', content);
      if (imageFile) {
        formData.append('image', imageFile);
      }
  
      const response = await fetch(`${API_URL}/sessions/${sessionId}/arguments/`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status}, message: ${JSON.stringify(errorData)}`);
      }
      const data = await response.json();
      console.log('Argument submitted successfully:', data);
      
      session.update(s => {
        if (s && s.id === sessionId) {
          console.log('Updating session with new argument');
          return {
            ...s,
            arguments: [...(s.arguments || []), data]
          };
        }
        return s;
      });
  
      // Check if this was the second argument
      session.update(s => {
        if (s && s.id === sessionId && s.arguments.length === 2) {
          // Trigger a re-render to show the "Waiting for judgement" message
          return { ...s, waitingForJudgement: true };
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
  try {
    const response = await fetch(`${API_URL}/sessions/${sessionId}/judge/`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    session.update(s => {
      if (s && s.id === sessionId) {
        s.judgement = data;
      }
      return s;
    });
    return data;
  } catch (error) {
    console.error("Error getting judgement:", error);
    throw error;
  }
}

export async function submitAppeal(sessionId, content) {
  try {
    const response = await fetch(`${API_URL}/sessions/${sessionId}/appeal/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    session.update(s => {
      if (s && s.id === sessionId) {
        s.appeals = [...(s.appeals || []), data];
        if (data.appeal_judgement) {
          s.appeal_judgement = data.appeal_judgement;
        }
      }
      return s;
    });
    return data;
  } catch (error) {
    console.error("Error submitting appeal:", error);
    throw error;
  }
}