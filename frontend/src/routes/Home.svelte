<script>
    import { createSession } from '../stores.js';
    import { navigate } from 'svelte-routing';
  
    let sessionName = '';
    let sessionDescription = '';
    let joinSessionId = '';
  
    async function handleCreateSession(event) {
      event.preventDefault();
      try {
        const newSession = await createSession(sessionName, sessionDescription);
        navigate(`/session/${newSession.id}`);
      } catch (error) {
        console.error('Error creating session:', error);
        alert('Failed to create session. Please try again.');
      }
    }
  
    function handleJoinSession(event) {
      event.preventDefault();
      if (joinSessionId) {
        navigate(`/session/${joinSessionId}`);
      } else {
        alert('Please enter a valid session ID or link');
      }
    }
  </script>
  
  <main>
    <h1>Welcome to AI Debate Judge</h1>
  
    <section>
      <h2>Create New Session</h2>
      <form on:submit={handleCreateSession}>
        <div>
          <label for="sessionName">Session Name:</label>
          <input id="sessionName" bind:value={sessionName} required>
        </div>
        <div>
          <label for="sessionDescription">Description:</label>
          <textarea id="sessionDescription" bind:value={sessionDescription}></textarea>
        </div>
        <button type="submit">Create Session</button>
      </form>
    </section>
  
    <section>
      <h2>Join Existing Session</h2>
      <form on:submit={handleJoinSession}>
        <div>
          <label for="joinSessionId">Session ID or Link:</label>
          <input id="joinSessionId" bind:value={joinSessionId} required>
        </div>
        <button type="submit">Join Session</button>
      </form>
    </section>
  </main>
  
  <style>
    main {
      max-width: 600px;
      margin: 0 auto;
      padding: 20px;
    }
  
    section {
      margin-bottom: 30px;
    }
  
    form {
      display: flex;
      flex-direction: column;
      gap: 15px;
    }
  
    input, textarea {
      width: 100%;
      padding: 5px;
    }
  
    button {
      padding: 10px 15px;
      background-color: #007bff;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
    }
  
    button:hover {
      background-color: #0056b3;
    }
  </style>