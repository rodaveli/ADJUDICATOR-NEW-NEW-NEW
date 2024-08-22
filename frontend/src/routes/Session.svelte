<script>
  import { onMount } from 'svelte';
  import { session, getSession, submitArgument, getJudgement, submitAppeal, inviteUser } from '../stores.js';

  export let id;
  let newArgument = '';
  let imageFile;
  let appealContent = '';
  let currentUser = 'user1'; // This should be dynamically set based on the current user
  let inviteEmail = '';
  let shareLink = `${window.location.origin}/session/${id}`;
  let messages = [];

  let socket;

onMount(async () => {
  await getSession(id);
  
  socket = new WebSocket(`ws://localhost:8000/ws/${id}`);
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    addMessage(data.message);
  };
});

  async function handleSubmitArgument(event) {
      event.preventDefault();
      try {
          const result = await submitArgument(id, newArgument, imageFile);
          addMessage(`${currentUser} submitted an argument`);
          newArgument = '';
          imageFile = null;
          $session = {...$session};
      } catch (error) {
          console.error('Error submitting argument:', error);
          alert('Failed to submit argument. Please try again.');
      }
  }

  async function copyShareLink() {
      try {
          await navigator.clipboard.writeText(shareLink);
          alert('Link copied to clipboard!');
      } catch (err) {
          console.error('Failed to copy: ', err);
      }
  }

  async function handleSubmitAppeal(event) {
      event.preventDefault();
      try {
          await submitAppeal(id, appealContent);
          addMessage(`${currentUser} submitted an appeal`);
          appealContent = '';
      } catch (error) {
          alert('Failed to submit appeal. Please try again.');
      }
  }

  async function handleInviteUser(event) {
      event.preventDefault();
      try {
          await inviteUser(id, inviteEmail);
          alert('User invited successfully!');
          inviteEmail = '';
      } catch (error) {
          alert('Failed to invite user. Please try again.');
      }
  }

  function getArgumentAuthor(index) {
      return index === 0 ? 'User 1' : 'User 2';
  }

  function addMessage(content) {
      messages = [...messages, { content, timestamp: new Date() }];
  }

  $: canSubmitArgument = $session?.arguments && $session.arguments.length < 2;
  $: canGetJudgement = $session?.arguments && $session.arguments.length === 2 && !$session?.judgement;
  $: canAppeal = $session?.judgement && $session.judgement.loser === currentUser && !$session.appeal_judgement;

  $: if ($session?.judgement) {
      addMessage(`Judgement: ${$session.judgement.winner} wins! Reason: ${$session.judgement.reasoning}`);
  }

  $: if ($session?.appeal_judgement) {
      addMessage(`Appeal Judgement: ${$session.appeal_judgement.winner} wins! Reason: ${$session.appeal_judgement.reasoning}`);
  }
</script>

<main>
  <h1>{$session?.name || 'Loading...'}</h1>
  <p>{$session?.description || 'No description available.'}</p>

  {#if $session?.judgement}
      <div class="judgement-result">
          <h2>Final Judgement</h2>
          <p class="winner">Winner: {$session.judgement.winner}</p>
          <p>Reasoning: {$session.judgement.reasoning}</p>
      </div>
  {/if}

  <section>
      <h2>Debate Chat</h2>
      <div class="chat-box">
          {#each messages as message}
              <p>{message.content}</p>
          {/each}
      </div>
  </section>

  <section>
      <h2>Invite Opponent</h2>
      <p>Share this link with your opponent:</p>
      <div class="share-link">
          <input type="text" readonly value={shareLink}>
          <button on:click={copyShareLink}>Copy Link</button>
      </div>
  </section>

  <section>
      <h2>Arguments</h2>
      {#if $session?.arguments && $session.arguments.length > 0}
          {#each $session.arguments as argument, index}
              <div class="argument">
                  <h3>Argument {index + 1} by {getArgumentAuthor(index)}</h3>
                  <p>{argument.content}</p>
                  {#if argument.image_url}
                      <img src={argument.image_url} alt="Argument image" />
                  {/if}
              </div>
          {/each}
      {:else}
          <p>No arguments submitted yet.</p>
      {/if}
  </section>

  {#if canSubmitArgument}
      <section>
          <h2>Submit Argument</h2>
          <form on:submit={handleSubmitArgument}>
              <div>
                  <label for="argument">Your Argument:</label>
                  <textarea id="argument" bind:value={newArgument} required></textarea>
              </div>
              <div>
                  <label for="image">Upload Image (optional):</label>
                  <input type="file" id="image" bind:files={imageFile} accept="image/*">
              </div>
              <button type="submit">Submit Argument</button>
          </form>
      </section>
  {:else if $session?.arguments?.length === 2 && !$session?.judgement}
      <section>
          <h2>Waiting for Judgement</h2>
          <p>Both arguments have been submitted. The AI judge is now evaluating them.</p>
      </section>
  {/if}

  {#if canAppeal}
      <section>
          <h2>Submit Appeal</h2>
          <form on:submit={handleSubmitAppeal}>
              <div>
                  <label for="appeal">Your Appeal:</label>
                  <textarea id="appeal" bind:value={appealContent} required></textarea>
              </div>
              <button type="submit">Submit Appeal</button>
          </form>
      </section>
  {/if}
</main>

<style>
  main {
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
  }

  section {
      margin-bottom: 30px;
  }

  .argument, .judgement, .appeal-judgement {
      border: 1px solid #ccc;
      padding: 15px;
      margin-bottom: 15px;
      border-radius: 5px;
  }

  .winner {
      color: green;
      font-size: 1.2em;
      font-weight: bold;
  }

  form {
      display: flex;
      flex-direction: column;
      gap: 15px;
  }

  textarea, input[type="email"] {
      width: 100%;
      padding: 10px;
  }

  textarea {
      height: 100px;
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

  img {
      max-width: 100%;
      height: auto;
      margin-top: 10px;
  }

  .chat-box {
      height: 300px;
      overflow-y: auto;
      border: 1px solid #ccc;
      padding: 10px;
      margin-bottom: 20px;
  }

  .judgement-result {
      background-color: #f0f0f0;
      padding: 20px;
      border-radius: 5px;
      margin-bottom: 20px;
  }
</style>