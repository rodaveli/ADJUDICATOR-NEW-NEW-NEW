<script>
    import { onMount, afterUpdate, onDestroy } from "svelte";
    import {
        session,
        getSession,
        submitArgument,
        getJudgement,
        submitAppeal,
        inviteUser,
        updateUsername,
        API_URL,
    } from "../stores.js";

    export let id;
    let newArgument = "";
    let imageFile;
    let appealContent = "";
    let currentUser = "user1"; // This should be dynamically set based on the current user
    let inviteEmail = "";
    let editingUsername = false;
    let newUsername = "";
    let shareLink = `${window.location.origin}/session/${id}`;
    let messages = [];
    let canAppeal = false;
    let appealSubmitted = false;

    let socket;

    onMount(async () => {
        console.log("Component mounted, fetching session:", id);
        await getSession(id);
        console.log("Session fetched:", $session);

        function connectWebSocket() {
            socket = new WebSocket(`ws://localhost:8000/ws/${id}`);
            socket.onopen = () => console.log("WebSocket connection opened");
            socket.onclose = (event) => {
                console.log("WebSocket connection closed", event);
                setTimeout(connectWebSocket, 1000); // Attempt to reconnect after 1 second
            };
            socket.onerror = (error) =>
                console.error("WebSocket error:", error);
            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log("Received WebSocket message:", data);
                if (data.message === "New argument submitted") {
                    addMessage(`New argument submitted`);
                    if (data.argumentCount === 2) {
                        addMessage(
                            "Both arguments submitted. Waiting for judgement...",
                        );
                    }
                    session.update((s) => ({
                        ...s,
                        arguments: [...(s.arguments || []), data.argument],
                    }));
                } else if (data.message === "Judgement ready") {
                    console.log("Received judgement:", data.judgement);
                    session.update((s) => ({
                        ...s,
                        judgement: data.judgement,
                    }));
                    addMessage(
                        `Judgement received: ${data.judgement.winner} wins!`,
                    );
                }
            };
        }

        connectWebSocket();
    });

    onDestroy(() => {
        if (socket) {
            socket.close();
        }
    });

    afterUpdate(() => {
        console.log("Component updated, current session state:", $session);
    });

    let userId;

    onMount(() => {
        userId = localStorage.getItem("userId");
        if (!userId) {
            userId = "user_" + Math.random().toString(36).substr(2, 9);
            localStorage.setItem("userId", userId);
        }
    });

    $: currentUser =
        userId === $session?.user1_id
            ? "user1"
            : userId === $session?.user2_id
              ? "user2"
              : null;

    function editUsername() {
        editingUsername = true;
        newUsername = $session[`${currentUser}_name`];
    }

    async function saveUsername() {
        try {
            const updatedSession = await updateUsername(
                id,
                currentUser,
                newUsername,
            );
            editingUsername = false;
        } catch (error) {
            console.error("Error updating username:", error);
            alert("Failed to update username. Please try again.");
        }
    }

    async function handleSubmitArgument(event) {
        event.preventDefault();
        try {
            const result = await submitArgument(id, newArgument, imageFile);
            addMessage(
                `${$session[`${currentUser}_name`]} submitted an argument`,
            );
            newArgument = "";
            imageFile = null;
            $session = { ...$session };
        } catch (error) {
            console.error("Error submitting argument:", error);
            alert("Failed to submit argument. Please try again.");
        }
    }

    async function copyShareLink() {
        try {
            await navigator.clipboard.writeText(shareLink);
            alert("Link copied to clipboard!");
        } catch (err) {
            console.error("Failed to copy: ", err);
        }
    }

    async function handleSubmitAppeal(event) {
        event.preventDefault();
        try {
            await submitAppeal(id, appealContent);
            addMessage(
                `${$session[`${currentUser}_name`]} submitted an appeal`,
            );
            appealContent = "";
        } catch (error) {
            alert("Failed to submit appeal. Please try again.");
        }
    }

    async function handleInviteUser(event) {
        event.preventDefault();
        try {
            await inviteUser(id, inviteEmail);
            alert("User invited successfully!");
            inviteEmail = "";
        } catch (error) {
            alert("Failed to invite user. Please try again.");
        }
    }

    function addMessage(content) {
        messages = [...messages, { content, timestamp: new Date() }];
        // Scroll to the bottom of the chat box
        const chatBox = document.querySelector(".chat-box");
        if (chatBox) {
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    $: canSubmitArgument = $session?.arguments && $session.arguments.length < 2;
    $: canGetJudgement =
        $session?.arguments &&
        $session.arguments.length === 2 &&
        !$session?.judgement;
    $: canAppeal =
        $session?.judgement &&
        $session.judgement.loser === $session[`${currentUser}_name`] && // Use username directly
        !$session.appeal_judgement;
</script>

<main>
    <h1>{$session?.name || "Loading..."}</h1>
    <p>{$session?.description || "No description available."}</p>

    <div class="user-info">
        {#if editingUsername}
            <input bind:value={newUsername} />
            <button on:click={saveUsername}>Save</button>
        {:else}
            <p>Your username: {$session?.[`${currentUser}_name`]}</p>
            <button on:click={editUsername}>Edit</button>
        {/if}
    </div>

    {#if $session?.judgement}
        <section>
            <h2>Judgement</h2>
            <div class="judgement">
                {#if $session.judgement.content.startsWith("An error occurred:")}
                    <p class="error">Error: {$session.judgement.content}</p>
                {:else}
                    <p>
                        <strong>Winner:</strong>
                        {$session.judgement.winning_user_id}
                    </p>
                    <p>
                        <strong>Winning Argument:</strong>
                        {$session.judgement.winning_argument}
                    </p>
                    <p>
                        <strong>Loser:</strong>
                        {$session.judgement.losing_user_id}
                    </p>
                    <p>
                        <strong>Losing Argument:</strong>
                        {$session.judgement.losing_argument}
                    </p>
                    <p>
                        <strong>Reasoning:</strong>
                        {$session.judgement.reasoning}
                    </p>
                {/if}
            </div>
        </section>

        {#if canAppeal}
            <section>
                <h2>Submit Appeal</h2>
                <form on:submit|preventDefault={handleSubmitAppeal}>
                    <textarea bind:value={appealContent} required></textarea>
                    <button type="submit">Submit Appeal</button>
                </form>
            </section>
        {/if}
    {/if}

    {#if $session?.appeal_judgement}
        <section>
            <h2>Appeal Judgement</h2>
            <div class="appeal-judgement">
                <p>
                    <strong>Winner:</strong>
                    {$session.appeal_judgement.winner}
                </p>
                <p>
                    <strong>Winning Argument:</strong>
                    {$session.appeal_judgement.winning_argument}
                </p>
                <p>
                    <strong>Loser:</strong>
                    {$session.appeal_judgement.loser}
                </p>
                <p>
                    <strong>Losing Argument:</strong>
                    {$session.appeal_judgement.losing_argument}
                </p>
                <p>
                    <strong>Reasoning:</strong>
                    {$session.appeal_judgement.reasoning}
                </p>
            </div>
        </section>
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
            <input type="text" readonly value={shareLink} />
            <button on:click={copyShareLink}>Copy Link</button>
        </div>
    </section>

    <section>
        <h2>Arguments</h2>
        {#if $session?.arguments && $session.arguments.length > 0}
            {#each $session.arguments as argument}
                <div class="argument">
                    <h3>Argument by {argument.username}</h3>
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
                    <textarea id="argument" bind:value={newArgument} required
                    ></textarea>
                </div>
                <div>
                    <label for="image">Upload Image (optional):</label>
                    <input
                        type="file"
                        id="image"
                        bind:files={imageFile}
                        accept="image/*"
                    />
                </div>
                <button type="submit">Submit Argument</button>
            </form>
        </section>
    {:else if $session?.arguments?.length === 2 && !$session?.judgement}
        <section>
            <h2>Waiting for Judgement</h2>
            <p>
                Both arguments have been submitted. The AI judge is now
                evaluating them.
            </p>
        </section>
    {/if}
</main>

<style>
    main {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    .judgement,
    .appeal-judgement {
        background-color: #f0f0f0;
        padding: 15px;
        border-radius: 5px;
        margin-top: 20px;
    }

    textarea {
        width: 100%;
        height: 100px;
        margin-bottom: 10px;
    }

    button {
        background-color: #4caf50;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }

    button:hover {
        background-color: #45a049;
    }

    section {
        margin-bottom: 30px;
    }

    .argument,
    .judgement,
    .appeal-judgement {
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

    textarea,
    input[type="email"] {
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
